"""Golden eval runner for Director Hub.

Loads every JSON file under `director_hub/evals/golden/`, sends each `input`
payload to the live Director Hub `/interpret_action` endpoint, and checks the
response against the per-scenario `expectations`. Designed to run against a
locally-booted Director Hub:

    uvicorn director_hub.bridge.server:app --port 7802  &
    python -m director_hub.evals.runner

Exit code is 0 if all scenarios pass, 1 if any fail. Per-scenario verdicts
print to stdout.

# Record/replay modes (golden-test reproducibility)

The agentic AI is non-deterministic by nature, so the runner supports
cassette-based replay for byte-identical reproducibility. The mode is
flipped via the DIRECTOR_HUB_REPLAY_MODE environment variable, which
the running Director Hub picks up at startup. Three workflows:

  --mode live (default)
      Run scenarios against whatever provider is configured. Useful
      for ad-hoc testing against the live LLM.

  --mode record
      Boot or restart Director Hub with DIRECTOR_HUB_REPLAY_MODE=record,
      run all scenarios, write a cassette per scenario into the cassette
      directory. The runner uses the existing /interpret_action endpoint
      so the wrapping happens server-side via the engine config override.

  --mode replay
      Boot Director Hub with DIRECTOR_HUB_REPLAY_MODE=replay. The runner
      sends scenarios as usual; the server returns the previously recorded
      response from disk. CassetteMiss → 500 → eval failure (loud, by
      design — replay misses should never silently fall through).

Note: --mode does NOT bounce the Director Hub for you. The intended
flow is to start Hub once with the desired DIRECTOR_HUB_REPLAY_MODE,
then run the eval runner against it. The flag exists in the runner so
CI can label its mode in logs.

Run via:
    python -m director_hub.evals.runner [--url URL] [--filter PATTERN] [--mode MODE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def load_scenarios(filter_pattern: str | None = None) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for path in sorted(GOLDEN_DIR.glob("*.json")):
        if filter_pattern and filter_pattern not in path.stem:
            continue
        scenarios.append(json.loads(path.read_text()))
    return scenarios


def check_expectations(
    response_status: int,
    response_body: dict[str, Any] | None,
    expectations: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Return (passed, failure_messages)."""
    failures: list[str] = []

    expected_status = expectations.get("expected_status", 200)
    if response_status != expected_status:
        failures.append(f"status: got {response_status}, expected {expected_status}")
        return False, failures

    if expected_status != 200:
        # Non-200 expectation. We don't validate the body.
        return True, failures

    if response_body is None:
        failures.append("response body was None")
        return False, failures

    if expectations.get("success_required") and not response_body.get("success"):
        failures.append(f"success was {response_body.get('success')}, expected True")

    scale = response_body.get("scale")
    if (smin := expectations.get("scale_min")) is not None:
        if scale is None or scale < smin:
            failures.append(f"scale {scale} below min {smin}")
    if (smax := expectations.get("scale_max")) is not None:
        if scale is None or scale > smax:
            failures.append(f"scale {scale} above max {smax}")

    nmin = expectations.get("narrative_min_length", 0)
    narrative = response_body.get("narrative_text", "")
    if len(narrative) < nmin:
        failures.append(f"narrative_text length {len(narrative)} below min {nmin}")

    forbidden = expectations.get("narrative_must_not_contain", [])
    for word in forbidden:
        if word.lower() in narrative.lower():
            failures.append(f"narrative_text contained forbidden substring: {word!r}")

    if expectations.get("stat_effects_must_be_empty"):
        effects = response_body.get("stat_effects") or []
        if effects:
            failures.append(f"stat_effects must be empty but got {effects}")

    # 'preferred_*' expectations are SOFT — they don't fail the eval but they
    # should be tracked once the real reasoning engine lands.
    return len(failures) == 0, failures


def run_scenario(client: httpx.Client, scenario: dict[str, Any]) -> tuple[bool, list[str]]:
    try:
        r = client.post("/interpret_action", json=scenario["input"])
    except httpx.RequestError as e:
        return False, [f"request error: {e}"]
    body = None
    if r.status_code == 200:
        try:
            body = r.json()
        except Exception as e:
            return False, [f"response not valid JSON: {e}"]
    return check_expectations(r.status_code, body, scenario.get("expectations", {}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:7802")
    ap.add_argument("--filter", default=None, help="substring filter on scenario id")
    ap.add_argument(
        "--mode",
        default="live",
        choices=("live", "record", "replay"),
        help="record/replay mode label (informational; the actual mode is "
        "set on the Director Hub via DIRECTOR_HUB_REPLAY_MODE)",
    )
    args = ap.parse_args()

    scenarios = load_scenarios(args.filter)
    if not scenarios:
        print("no scenarios matched", file=sys.stderr)
        return 1

    print(f"running {len(scenarios)} eval scenarios against {args.url} (mode={args.mode})")
    print()

    passed = 0
    failed = 0
    with httpx.Client(base_url=args.url, timeout=10.0) as client:
        # Health check first so we fail fast if the service is down.
        try:
            health = client.get("/health")
            if health.status_code != 200:
                print(f"FATAL: /health returned {health.status_code}", file=sys.stderr)
                return 1
        except httpx.RequestError as e:
            print(f"FATAL: cannot reach Director Hub at {args.url}: {e}", file=sys.stderr)
            return 1

        for scenario in scenarios:
            ok, failures = run_scenario(client, scenario)
            label = f"[{scenario['id']}] ({scenario.get('category', '?')})"
            if ok:
                print(f"PASS {label}")
                passed += 1
            else:
                print(f"FAIL {label}")
                for f in failures:
                    print(f"     {f}")
                failed += 1

    print()
    print(f"total: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
