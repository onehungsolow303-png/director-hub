"""Score and select the best encounter template for a given context."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from director_hub.content.template_store import EncounterTemplate

if TYPE_CHECKING:
    from director_hub.content.template_store import TemplateStore
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)

# Default scoring weights (configurable via models.yaml)
_WEIGHTS = {
    "party_composition": 0.3,
    "narrative_connection": 0.25,
    "memory_informed": 0.25,
    "freshness": 0.2,
}


class EncounterSelector:
    def __init__(
        self,
        store: TemplateStore,
        memory: MemoryManager,
        weights: dict[str, float] | None = None,
        min_score: float = 0.3,
    ) -> None:
        self._store = store
        self._memory = memory
        self._weights = weights or _WEIGHTS
        self._min_score = min_score

    def select(
        self,
        biome: str,
        party: list[dict[str, Any]],
        xp_budget: int,
        scene_context: dict[str, Any],
    ) -> EncounterTemplate | None:
        """Select the best-fit template. Returns None if no template scores above minimum."""
        party_size = max(len(party), 1)
        candidates = self._filter(biome, party_size, xp_budget)

        if not candidates:
            return None

        scored = [(tpl, self._score(tpl, party, scene_context)) for tpl in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_tpl, best_score = scored[0]
        if best_score < self._min_score:
            log.info(
                "No template scored above %.2f (best: %s at %.2f)",
                self._min_score,
                best_tpl.template_id,
                best_score,
            )
            return None

        log.info("Selected template %s (score=%.2f)", best_tpl.template_id, best_score)
        return best_tpl

    def _filter(self, biome: str, party_size: int, xp_budget: int) -> list[EncounterTemplate]:
        results = []
        for tpl in self._store.all():
            if biome not in tpl.biomes:
                continue
            if party_size < tpl.party_size_range[0] or party_size > tpl.party_size_range[1]:
                continue
            if tpl.min_xp > xp_budget:
                continue
            results.append(tpl)
        return results

    def _score(
        self,
        tpl: EncounterTemplate,
        party: list[dict[str, Any]],
        scene_context: dict[str, Any],
    ) -> float:
        w = self._weights
        score = 0.0

        # Party composition match
        score += w["party_composition"] * self._score_party_match(tpl, party)

        # Narrative connection
        score += w["narrative_connection"] * self._score_narrative(tpl, scene_context)

        # Memory-informed (confidence + average_outcome)
        score += w["memory_informed"] * self._score_memory(tpl)

        # Freshness (less used = higher score)
        score += w["freshness"] * self._score_freshness(tpl)

        return score

    @staticmethod
    def _score_party_match(tpl: EncounterTemplate, party: list[dict[str, Any]]) -> float:
        if not party or not tpl.party_counters:
            return 0.5  # Neutral if no composition data

        classes = {p.get("class", "").lower() for p in party}
        has_melee = bool(classes & {"fighter", "barbarian", "paladin", "monk"})
        has_ranged = bool(classes & {"ranger", "rogue"})
        has_magic = bool(classes & {"wizard", "sorcerer", "warlock", "bard", "druid"})
        has_healer = bool(classes & {"cleric", "druid", "paladin", "bard"})

        party_traits = set()
        if has_melee and not has_ranged and not has_magic:
            party_traits.add("all_melee")
        if not has_healer:
            party_traits.add("no_healer")
        if has_ranged:
            party_traits.add("has_ranged")
        if has_melee and has_ranged and has_magic:
            party_traits.add("balanced_party")

        # Template counters match party weaknesses = challenging (good)
        counter_overlap = len(set(tpl.party_counters) & party_traits)
        # Template rewards match party strengths = too easy (bad)
        reward_overlap = len(set(tpl.party_rewards) & party_traits)

        return min(1.0, max(0.0, 0.5 + counter_overlap * 0.25 - reward_overlap * 0.15))

    @staticmethod
    def _score_narrative(tpl: EncounterTemplate, scene_context: dict[str, Any]) -> float:
        score = 0.0
        traveling_to = (scene_context.get("traveling_to") or "").lower()
        active_quest = (scene_context.get("active_quest") or "").lower()
        tags_lower = {t.lower() for t in tpl.tags}
        hook_lower = tpl.narrative_hook.lower()

        for context_word in traveling_to.split() + active_quest.split():
            if not context_word or len(context_word) < 3:
                continue
            if context_word in tags_lower or context_word in hook_lower:
                score += 0.3

        return min(1.0, score)

    @staticmethod
    def _score_memory(tpl: EncounterTemplate) -> float:
        if tpl.average_outcome is not None:
            return tpl.average_outcome * tpl.confidence
        return tpl.confidence * 0.5

    @staticmethod
    def _score_freshness(tpl: EncounterTemplate) -> float:
        if tpl.times_used == 0:
            return 1.0
        return max(0.0, 1.0 - tpl.times_used * 0.1)
