"""Record and retrieve LLM predictions for outcome comparison."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_DEFAULT_ROOT = Path("C:/Dev/.shared/state/predictions")


@dataclass
class Prediction:
    decision_id: str
    session_id: str
    decision_type: str = "unknown"
    expected_difficulty: str = "medium"
    expected_player_reaction: str = "engage_combat"
    expected_outcome: str = "player_wins_with_damage"
    confidence: float = 0.5
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class PredictionRecorder:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or _DEFAULT_ROOT
        self._root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Prediction] = {}

    def record(self, prediction: Prediction) -> None:
        path = self._root / f"{prediction.session_id}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(prediction), default=str) + "\n")
        self._cache[prediction.session_id] = prediction

    def get_latest(self, session_id: str) -> Prediction | None:
        if session_id in self._cache:
            return self._cache[session_id]
        path = self._root / f"{session_id}.jsonl"
        if not path.exists():
            return None
        last_line = ""
        for line in open(path, encoding="utf-8"):  # noqa: SIM115
            line = line.strip()
            if line:
                last_line = line
        if not last_line:
            return None
        data = json.loads(last_line)
        pred = Prediction(**{k: v for k, v in data.items() if k in Prediction.__dataclass_fields__})
        self._cache[session_id] = pred
        return pred

    def all_for_session(self, session_id: str) -> list[Prediction]:
        path = self._root / f"{session_id}.jsonl"
        if not path.exists():
            return []
        results = []
        for line in open(path, encoding="utf-8"):  # noqa: SIM115
            line = line.strip()
            if line:
                data = json.loads(line)
                results.append(
                    Prediction(
                        **{k: v for k, v in data.items() if k in Prediction.__dataclass_fields__}
                    )
                )
        return results

    @staticmethod
    def extract_from_response(
        response: dict[str, Any],
        session_id: str,
        decision_id: str,
    ) -> Prediction | None:
        raw = response.get("_prediction")
        if not raw or not isinstance(raw, dict):
            return None
        return Prediction(
            decision_id=decision_id,
            session_id=session_id,
            decision_type=raw.get("decision_type", "unknown"),
            expected_difficulty=raw.get("expected_difficulty", "medium"),
            expected_player_reaction=raw.get("expected_player_reaction", "unknown"),
            expected_outcome=raw.get("expected_outcome", "unknown"),
            confidence=raw.get("confidence", 0.5),
        )

    @staticmethod
    def strip_from_response(response: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in response.items() if k != "_prediction"}
