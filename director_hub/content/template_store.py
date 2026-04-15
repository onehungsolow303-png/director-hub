"""Encounter template storage — JSON files + long-term memory index."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)

_DEFAULT_DIR = Path("C:/Dev/.shared/state/encounter_templates")


@dataclass
class EncounterTemplate:
    template_id: str
    name: str
    min_xp: int = 100
    max_xp: int = 300
    party_size_range: list[int] = field(default_factory=lambda: [1, 4])
    biomes: list[str] = field(default_factory=lambda: ["forest"])
    slots: list[dict[str, Any]] = field(default_factory=list)
    scaling: dict[str, Any] = field(default_factory=dict)
    party_counters: list[str] = field(default_factory=list)
    party_rewards: list[str] = field(default_factory=list)
    narrative_hook: str = ""
    design_intent: str = ""
    difficulty_context: str = ""
    tags: list[str] = field(default_factory=list)
    generated_by: str = "director_hub"
    confidence: float = 0.7
    times_used: int = 0
    average_outcome: float | None = None


class TemplateStore:
    def __init__(
        self,
        template_dir: Path | None = None,
        memory: MemoryManager | None = None,
    ) -> None:
        self._dir = template_dir or _DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._memory = memory
        self._cache: dict[str, EncounterTemplate] = {}
        self._load_all()

    def _load_all(self) -> None:
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                tpl = EncounterTemplate(
                    **{k: v for k, v in data.items() if k in EncounterTemplate.__dataclass_fields__}
                )
                self._cache[tpl.template_id] = tpl
            except Exception:
                log.warning("Failed to load template %s", path.name)

    def save(self, template: EncounterTemplate) -> None:
        path = self._dir / f"{template.template_id}.json"
        path.write_text(json.dumps(asdict(template), indent=2, default=str), encoding="utf-8")
        self._cache[template.template_id] = template

        if self._memory:
            search_text = f"{template.name} {template.design_intent} {template.difficulty_context} {' '.join(template.tags)}"
            self._memory.long.index(
                {
                    "text": search_text,
                    "category": "encounter_template",
                    "template_id": template.template_id,
                    "biomes": template.biomes,
                    "party_counters": template.party_counters,
                    "confidence": template.confidence,
                    "metadata": {"template_id": template.template_id},
                }
            )

    def get(self, template_id: str) -> EncounterTemplate | None:
        return self._cache.get(template_id)

    def all(self) -> list[EncounterTemplate]:
        return list(self._cache.values())

    def list_by_biome(self, biome: str) -> list[EncounterTemplate]:
        return [t for t in self._cache.values() if biome in t.biomes]

    def record_usage(self, template_id: str, outcome_quality: float) -> None:
        tpl = self._cache.get(template_id)
        if not tpl:
            return
        tpl.times_used += 1
        if tpl.average_outcome is None:
            tpl.average_outcome = outcome_quality
        else:
            tpl.average_outcome = (
                tpl.average_outcome * (tpl.times_used - 1) + outcome_quality
            ) / tpl.times_used
        self.save(tpl)

    def update_confidence(self, template_id: str, delta: float) -> None:
        tpl = self._cache.get(template_id)
        if not tpl:
            return
        tpl.confidence = max(0.0, min(1.0, tpl.confidence + delta))
        self.save(tpl)

    def prune(self, confidence_threshold: float = 0.3, min_uses: int = 3) -> list[str]:
        pruned: list[str] = []
        for tid, tpl in list(self._cache.items()):
            if tpl.generated_by == "hard_coded":
                continue
            if tpl.confidence < confidence_threshold and tpl.times_used >= min_uses:
                path = self._dir / f"{tid}.json"
                if path.exists():
                    path.unlink()
                del self._cache[tid]
                pruned.append(tid)
                log.info(
                    "Pruned template %s (confidence=%.2f, used=%d)",
                    tid,
                    tpl.confidence,
                    tpl.times_used,
                )
        return pruned

    def count(self) -> int:
        return len(self._cache)

    def gap_analysis(self, biomes: list[str] | None = None) -> dict[str, Any]:
        all_tpls = self.all()
        biome_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}
        counter_counts: dict[str, int] = {}

        for t in all_tpls:
            for b in t.biomes:
                biome_counts[b] = biome_counts.get(b, 0) + 1
            for tag in t.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            for c in t.party_counters:
                counter_counts[c] = counter_counts.get(c, 0) + 1

        missing_biomes = [b for b in (biomes or []) if biome_counts.get(b, 0) < 2]

        return {
            "total": len(all_tpls),
            "biome_counts": biome_counts,
            "tag_counts": tag_counts,
            "counter_counts": counter_counts,
            "missing_biomes": missing_biomes,
        }
