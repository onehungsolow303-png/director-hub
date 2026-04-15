"""Generate new encounter templates via LLM or deterministic fallback."""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

from director_hub.content.template_store import EncounterTemplate

if TYPE_CHECKING:
    from director_hub.content.template_store import TemplateStore
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)

# Enemy pools by biome for deterministic fallback
_ENEMY_POOLS: dict[str, list[dict[str, Any]]] = {
    "forest": [
        {"name": "Wolf", "behavior": "chase", "xp": 25, "damage_type": "piercing"},
        {"name": "Bandit", "behavior": "chase", "xp": 50, "damage_type": "slashing"},
        {"name": "Bandit Archer", "behavior": "ranged", "xp": 50, "damage_type": "piercing"},
        {"name": "Orc", "behavior": "chase", "xp": 100, "damage_type": "slashing"},
    ],
    "swamp": [
        {"name": "Bog Zombie", "behavior": "chase", "xp": 50, "damage_type": "bludgeoning"},
        {"name": "Swamp Hag", "behavior": "ranged", "xp": 200, "damage_type": "necrotic"},
        {"name": "Giant Toad", "behavior": "chase", "xp": 100, "damage_type": "bludgeoning"},
    ],
    "dungeon": [
        {"name": "Skeleton", "behavior": "guard", "xp": 50, "damage_type": "slashing"},
        {"name": "Mummy", "behavior": "chase", "xp": 200, "damage_type": "necrotic"},
        {"name": "Skeleton Archer", "behavior": "ranged", "xp": 50, "damage_type": "piercing"},
    ],
    "plains": [
        {"name": "Gnoll", "behavior": "chase", "xp": 100, "damage_type": "piercing"},
        {"name": "Cultist", "behavior": "ranged", "xp": 50, "damage_type": "necrotic"},
        {"name": "Hyena", "behavior": "chase", "xp": 25, "damage_type": "piercing"},
    ],
    "ruins": [
        {"name": "Wraith", "behavior": "chase", "xp": 200, "damage_type": "necrotic"},
        {"name": "Cursed Knight", "behavior": "guard", "xp": 200, "damage_type": "slashing"},
        {"name": "Ghost", "behavior": "ranged", "xp": 100, "damage_type": "necrotic"},
    ],
}


class EncounterDesigner:
    def __init__(
        self,
        store: TemplateStore,
        memory: MemoryManager,
        max_templates: int = 100,
    ) -> None:
        self._store = store
        self._memory = memory
        self._max_templates = max_templates

    def design(
        self,
        gaps: dict[str, Any],
        player_context: dict[str, Any],
        lessons: list[str],
        use_llm: bool = True,
        max_new: int = 3,
    ) -> list[EncounterTemplate]:
        """Generate new encounter templates to fill library gaps."""
        # Prune if at capacity
        if self._store.count() >= self._max_templates:
            self._store.prune(confidence_threshold=0.3, min_uses=3)

        if self._store.count() >= self._max_templates:
            log.warning("Template store at capacity (%d), cannot add more", self._store.count())
            return []

        if use_llm:
            return self._design_with_llm(gaps, player_context, lessons, max_new)
        return self._design_deterministic(gaps, player_context, max_new)

    def _design_deterministic(
        self,
        gaps: dict[str, Any],
        player_context: dict[str, Any],
        max_new: int,
    ) -> list[EncounterTemplate]:
        """Deterministic template generation — builds from enemy pools."""
        templates: list[EncounterTemplate] = []
        missing_biomes = gaps.get("missing_biomes", [])

        for biome in missing_biomes[:max_new]:
            pool = _ENEMY_POOLS.get(biome, _ENEMY_POOLS["forest"])
            tid = f"gen_{biome}_{uuid.uuid4().hex[:8]}"

            # Pick 2-3 enemies from pool
            slots = []
            total_xp = 0
            for enemy in pool[:3]:
                slots.append(enemy.copy())
                total_xp += enemy["xp"]

            tpl = EncounterTemplate(
                template_id=tid,
                name=f"{biome.title()} Encounter",
                min_xp=max(50, total_xp - 50),
                max_xp=total_xp + 100,
                party_size_range=[1, 4],
                biomes=[biome],
                slots=slots,
                scaling={"per_extra_player": {"add_slot": pool[0].copy()}, "max_slots": 6},
                party_counters=self._infer_counters(slots),
                party_rewards=self._infer_rewards(slots),
                narrative_hook=f"Enemies lurk in the {biome}",
                design_intent=f"Fill gap: no {biome} encounters in library",
                difficulty_context=f"Level {player_context.get('level', 2)}-{player_context.get('level', 2) + 2}",
                tags=[biome] + [s["name"].lower().split()[0] for s in slots],
                generated_by="director_hub",
                confidence=0.5,
            )

            self._store.save(tpl)
            templates.append(tpl)

        return templates

    def _design_with_llm(
        self,
        gaps: dict[str, Any],
        player_context: dict[str, Any],
        lessons: list[str],
        max_new: int,
    ) -> list[EncounterTemplate]:
        """LLM-powered template generation using Sonnet."""
        try:
            import anthropic as anthropic_sdk

            from director_hub.reasoning.providers.anthropic import _resolve_anthropic_key
        except (ImportError, Exception):
            log.warning("LLM unavailable for encounter design, falling back to deterministic")
            return self._design_deterministic(gaps, player_context, max_new)

        api_key = _resolve_anthropic_key()
        if not api_key:
            return self._design_deterministic(gaps, player_context, max_new)

        library_summary = json.dumps(self._store.gap_analysis(), indent=2)
        lessons_text = (
            "\n".join(f"- {lesson}" for lesson in lessons[:10]) if lessons else "None yet"
        )

        prompt = (
            f"You are a game encounter designer. Generate {max_new} new encounter templates.\n\n"
            f"Library state:\n{library_summary}\n\n"
            f"Player context: {json.dumps(player_context)}\n\n"
            f"Lessons learned:\n{lessons_text}\n\n"
            f"Gaps to fill: {json.dumps(gaps)}\n\n"
            f"Output a JSON array of templates. Each must have:\n"
            f"template_id, name, min_xp, max_xp, party_size_range, biomes, slots (array of "
            f'{{"name", "behavior", "xp", "damage_type"}}), scaling, party_counters, party_rewards, '
            f"narrative_hook, design_intent, difficulty_context, tags\n\n"
            f"Behaviors: chase, guard, ranged, coward\n"
            f"Damage types: slashing, piercing, bludgeoning, fire, cold, necrotic, radiant, poison\n"
        )

        try:
            client = anthropic_sdk.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text if resp.content else "[]"

            # Parse JSON array from response
            from director_hub.reasoning.providers.anthropic import _extract_json_object

            # Try array first
            start = text.find("[")
            if start >= 0:
                end = text.rfind("]")
                if end > start:
                    raw_list = json.loads(text[start : end + 1])
                else:
                    raw_list = []
            else:
                obj = _extract_json_object(text)
                raw_list = [obj] if obj else []

            templates = []
            for raw in raw_list[:max_new]:
                if not isinstance(raw, dict) or "template_id" not in raw:
                    raw["template_id"] = f"gen_llm_{uuid.uuid4().hex[:8]}"
                raw["generated_by"] = "director_hub"
                raw["confidence"] = 0.6
                raw["times_used"] = 0
                raw["average_outcome"] = None

                tpl = EncounterTemplate(
                    **{k: v for k, v in raw.items() if k in EncounterTemplate.__dataclass_fields__}
                )
                self._store.save(tpl)
                templates.append(tpl)

            return templates

        except Exception:
            log.exception("LLM encounter design failed, falling back to deterministic")
            return self._design_deterministic(gaps, player_context, max_new)

    @staticmethod
    def _infer_counters(slots: list[dict]) -> list[str]:
        has_ranged = any(s.get("behavior") == "ranged" for s in slots)
        counters = []
        if has_ranged:
            counters.append("all_melee")
        if any(s.get("damage_type") == "necrotic" for s in slots):
            counters.append("no_healer")
        return counters

    @staticmethod
    def _infer_rewards(slots: list[dict]) -> list[str]:
        rewards = []
        if all(s.get("behavior") == "chase" for s in slots):
            rewards.append("has_ranged")
        return rewards
