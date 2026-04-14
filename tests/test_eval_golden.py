"""Run the golden eval suite against the in-process FastAPI TestClient.

This wraps director_hub/evals/runner.check_expectations so the same logic
that the live runner uses is also exercised by pytest, without needing
the uvicorn server to be booted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from director_hub.evals.runner import GOLDEN_DIR, check_expectations

SCENARIOS = sorted(GOLDEN_DIR.glob("*.json"))


@pytest.mark.parametrize("scenario_path", SCENARIOS, ids=lambda p: p.stem)
def test_golden_scenario(client, scenario_path: Path):
    scenario = json.loads(scenario_path.read_text())
    payload = scenario["input"]

    r = client.post("/interpret_action", json=payload)
    body = r.json() if r.status_code == 200 else None

    ok, failures = check_expectations(
        r.status_code,
        body,
        scenario.get("expectations", {}),
    )

    assert ok, f"{scenario['id']} failed: {failures}"
