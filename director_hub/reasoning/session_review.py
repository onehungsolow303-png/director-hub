"""Deep session-end review — consolidates lessons and promotes patterns to rules."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)

_PROMOTION_THRESHOLD = 3


class SessionReviewer:
    def __init__(
        self, manager: MemoryManager, promotion_threshold: int = _PROMOTION_THRESHOLD
    ) -> None:
        self._mgr = manager
        self._threshold = promotion_threshold

    def review(self, session_id: str, use_llm: bool = True) -> dict[str, Any]:
        events = self._mgr.episodic.for_session(session_id)
        if not events:
            return {
                "session_id": session_id,
                "events_reviewed": 0,
                "session_summary": "Empty session",
            }

        if use_llm:
            return self._review_with_llm(session_id, events)
        return self._review_deterministic(session_id, events)

    def _review_deterministic(self, session_id: str, events: list[dict]) -> dict[str, Any]:
        summary_parts: list[str] = []
        promotions: list[dict] = []
        new_entries: list[str] = []

        combat_events = [e for e in events if e.get("type", "").startswith("combat")]
        quest_events = [e for e in events if "quest" in e.get("type", "")]
        skipped = [e for e in events if "skip" in e.get("type", "")]

        if combat_events:
            summary_parts.append(f"{len(combat_events)} combat events")
        if quest_events:
            summary_parts.append(f"{len(quest_events)} quest events")
        if skipped:
            summary_parts.append(f"{len(skipped)} content skipped")
            lesson = f"Player skipped {len(skipped)} content items in session {session_id}"
            new_entries.append(lesson)
            self._mgr.long.index(
                {"text": lesson, "category": "session_pattern", "metadata": {"confirmed_count": 1}}
            )

        all_journal = self._mgr.long.search("lesson", k=50)
        for entry in all_journal:
            meta = entry.get("metadata", {})
            if isinstance(meta, dict):
                count = meta.get("confirmed_count", 0)
                if count >= self._threshold:
                    text = entry.get("text", "")
                    key = self._make_rule_key(text)
                    if not self._mgr.semantic.get(key):
                        self._mgr.semantic.set(key, text)
                        promotions.append({"key": key, "value": text, "confirmations": count})
                        log.info("Promoted lesson to rule: %s", key)

        # Encounter design pass: generate templates to fill gaps
        try:
            from director_hub.content.encounter_designer import EncounterDesigner
            from director_hub.content.template_store import TemplateStore

            store = TemplateStore(memory=self._mgr)
            likely_biomes: list[str] = []
            intentions = self._mgr.semantic.get("_next_session_intentions") or []
            if isinstance(intentions, list):
                for intent in intentions:
                    for biome in ("forest", "swamp", "dungeon", "plains", "ruins", "castle"):
                        if biome in str(intent).lower():
                            likely_biomes.append(biome)

            gaps = store.gap_analysis(biomes=likely_biomes)
            if gaps.get("missing_biomes"):
                designer = EncounterDesigner(store, self._mgr)
                new_templates = designer.design(
                    gaps=gaps,
                    player_context={},
                    lessons=new_entries,
                    use_llm=False,
                )
                if new_templates:
                    summary_parts.append(f"{len(new_templates)} encounter templates generated")
        except Exception:
            log.exception("Encounter design pass failed")

        session_summary = "; ".join(summary_parts) if summary_parts else "Routine session"

        return {
            "session_id": session_id,
            "events_reviewed": len(events),
            "session_summary": session_summary,
            "new_journal_entries": new_entries,
            "promotions": promotions,
        }

    def _review_with_llm(self, session_id: str, events: list[dict]) -> dict[str, Any]:
        try:
            import anthropic as anthropic_sdk

            from director_hub.reasoning.providers.anthropic import _resolve_anthropic_key
        except (ImportError, Exception):
            log.warning("LLM unavailable for session review, falling back to deterministic")
            return self._review_deterministic(session_id, events)

        api_key = _resolve_anthropic_key()
        if not api_key:
            return self._review_deterministic(session_id, events)

        events_text = "\n".join(
            f"- {e.get('type', 'event')}: {json.dumps({k: v for k, v in e.items() if k != 'session_id'}, default=str)[:200]}"
            for e in events[-30:]
        )

        rules_text = "\n".join(f"- {k}: {v}" for k, v in self._mgr.semantic.all().items())

        prompt = (
            f"You are reviewing your performance as game director for session {session_id}.\n\n"
            f"Session events:\n{events_text}\n\n"
            f"Current rules:\n{rules_text or 'None yet'}\n\n"
            f"Analyze and output JSON:\n"
            f'{{"session_summary": "1-2 sentences",'
            f'"new_lessons": ["lesson1"],'
            f'"promote_to_rules": [{{"key": "rule_key", "value": "rule text"}}],'
            f'"revise_rules": [{{"key": "existing_key", "new_value": "updated text"}}],'
            f'"remove_rules": ["key_to_remove"],'
            f'"next_session_intentions": ["intention1"]}}'
        )

        try:
            client = anthropic_sdk.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text if resp.content else ""

            from director_hub.reasoning.providers.anthropic import _extract_json_object

            parsed = _extract_json_object(text)

            if not parsed:
                return self._review_deterministic(session_id, events)

            for lesson in parsed.get("new_lessons", []):
                self._mgr.long.index(
                    {
                        "text": lesson,
                        "category": "session_lesson",
                        "metadata": {"confirmed_count": 1},
                    }
                )

            for rule in parsed.get("promote_to_rules", []):
                if rule.get("key") and rule.get("value"):
                    self._mgr.semantic.set(rule["key"], rule["value"])

            for rule in parsed.get("revise_rules", []):
                if rule.get("key") and rule.get("new_value"):
                    self._mgr.semantic.set(rule["key"], rule["new_value"])

            for key in parsed.get("remove_rules", []):
                self._mgr.semantic.delete(key)

            if parsed.get("next_session_intentions"):
                self._mgr.semantic.set(
                    "_next_session_intentions", parsed["next_session_intentions"]
                )

            # Encounter design pass: generate templates to fill gaps
            new_entries: list[str] = parsed.get("new_lessons", [])
            summary_parts: list[str] = []
            try:
                from director_hub.content.encounter_designer import EncounterDesigner
                from director_hub.content.template_store import TemplateStore

                store = TemplateStore(memory=self._mgr)
                likely_biomes: list[str] = []
                intentions = self._mgr.semantic.get("_next_session_intentions") or []
                if isinstance(intentions, list):
                    for intent in intentions:
                        for biome in (
                            "forest",
                            "swamp",
                            "dungeon",
                            "plains",
                            "ruins",
                            "castle",
                        ):
                            if biome in str(intent).lower():
                                likely_biomes.append(biome)

                gaps = store.gap_analysis(biomes=likely_biomes)
                if gaps.get("missing_biomes"):
                    designer = EncounterDesigner(store, self._mgr)
                    new_templates = designer.design(
                        gaps=gaps,
                        player_context={},
                        lessons=new_entries,
                        use_llm=False,
                    )
                    if new_templates:
                        summary_parts.append(f"{len(new_templates)} encounter templates generated")
            except Exception:
                log.exception("Encounter design pass failed")

            session_summary = parsed.get("session_summary", "")
            if summary_parts:
                session_summary += "; " + "; ".join(summary_parts)

            return {
                "session_id": session_id,
                "events_reviewed": len(events),
                "session_summary": session_summary,
                "llm_used": True,
                **{k: v for k, v in parsed.items() if k != "session_summary"},
            }

        except Exception:
            log.exception("LLM session review failed, falling back to deterministic")
            return self._review_deterministic(session_id, events)

    @staticmethod
    def _make_rule_key(text: str) -> str:
        words = text.lower().split()[:5]
        return "_".join(w for w in words if w.isalnum())[:40]
