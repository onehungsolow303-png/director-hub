"""Production Quality Loop — Automated improvement coordinator.

Runs a 10-iteration improvement loop:
1. Regression gate (full 42-test suite)
2. Production test (Enhanced canvas vs user reference)
3. If failing: dispatch fix agent with escalating scope
4. Repeat until quality targets met or iterations exhausted

Usage:
    .venv/Scripts/python.exe tests/production_loop.py

Requires: server running at http://127.0.0.1:8080
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Dev\Image generator")
VENV_PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")
REPORTS_DIR = ROOT / "tests" / "reports"
ITERATIONS_PATH = REPORTS_DIR / "production_iterations.json"
PROD_REPORT_PATH = REPORTS_DIR / "production_report.json"

MAX_ITERATIONS = 10
PLATEAU_TRIGGER = 3

TIERS = {
    1: {"alpha_iou_min": 0.90, "ssim_min": 0.30, "alpha_mae_max": 12.0},
    2: {"alpha_iou_min": 0.93, "ssim_min": 0.40, "alpha_mae_max": 8.0},
    3: {"alpha_iou_min": 0.95, "ssim_min": 0.50, "alpha_mae_max": 5.0},
}


def get_tier(iteration):
    """Get quality tier for a given iteration number."""
    if iteration <= 3:
        return 1
    if iteration <= 6:
        return 2
    return 3


def get_scope(iteration):
    """Get escalation scope for a given iteration number."""
    if iteration <= 3:
        return "params"
    if iteration <= 6:
        return "post-process"
    return "structural"


def load_state():
    """Load or initialize loop state."""
    if ITERATIONS_PATH.exists():
        with open(ITERATIONS_PATH) as f:
            return json.load(f)
    return {
        "current_iteration": 1,
        "current_tier": 1,
        "focus": "dark",
        "history": [],
        "best_dark": None,
        "best_light": None,
    }


def save_state(state):
    """Save loop state to disk."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ITERATIONS_PATH, "w") as f:
        json.dump(state, f, indent=2)


def run_regression():
    """Run full 42-test regression suite. Returns True if all pass."""
    print("\n══ REGRESSION GATE ══")
    result = subprocess.run(
        [VENV_PYTHON, "-m", "pytest",
         "tests/test_smoke.py", "tests/test_unit_metrics.py",
         "tests/test_live_extraction.py", "tests/test_quality_gates.py",
         "-v", "--tb=short", "-x"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    passed = result.returncode == 0
    print(f"  Regression: {'PASS' if passed else 'FAIL'}")
    if not passed:
        print(f"  stdout: {result.stdout[-500:]}")
        print(f"  stderr: {result.stderr[-500:]}")
    return passed


def run_production_test():
    """Run production test. Returns metrics dict or None on failure."""
    print("\n══ PRODUCTION TEST ══")
    result = subprocess.run(
        [VENV_PYTHON, "-m", "pytest",
         "tests/test_production.py", "-v", "--tb=short"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    print(f"  Production test exit code: {result.returncode}")
    if result.stdout:
        for line in result.stdout.split("\n"):
            if "PASSED" in line or "FAILED" in line or "Production" in line:
                print(f"  {line.strip()}")

    if PROD_REPORT_PATH.exists():
        with open(PROD_REPORT_PATH) as f:
            return json.load(f)
    return None


def check_targets(metrics, tier):
    """Check if metrics meet the tier targets. Returns (passed, details)."""
    thresholds = TIERS.get(tier, TIERS[1])

    failures = []
    for key in ["dark", "light"]:
        m = metrics.get(key)
        if m is None:
            failures.append(f"{key}: no data")
            continue
        if m["alpha_iou"] < thresholds["alpha_iou_min"]:
            failures.append(f"{key}_iou={m['alpha_iou']:.4f} (need {thresholds['alpha_iou_min']})")
        if m["ssim"] < thresholds["ssim_min"]:
            failures.append(f"{key}_ssim={m['ssim']:.4f} (need {thresholds['ssim_min']})")
        if m["alpha_mae"] > thresholds["alpha_mae_max"]:
            failures.append(f"{key}_mae={m['alpha_mae']:.2f} (need <= {thresholds['alpha_mae_max']})")

    return len(failures) == 0, failures


def print_metrics(metrics):
    """Print current metrics summary."""
    for key in ["dark", "light"]:
        m = metrics.get(key)
        if m:
            print(f"  {key}: IoU={m['alpha_iou']:.4f}  SSIM={m['ssim']:.4f}  MAE={m['alpha_mae']:.2f}")
        else:
            print(f"  {key}: no data")


def main():
    print("═══════════════════════════════════════════════════")
    print("  Gut It Out — Production Quality Loop")
    print("  Max iterations: 10 | Dark first, then light")
    print("═══════════════════════════════════════════════════")

    state = load_state()
    no_improvement_count = 0

    while state["current_iteration"] <= MAX_ITERATIONS:
        iteration = state["current_iteration"]
        tier = get_tier(iteration)
        scope = get_scope(iteration)
        state["current_tier"] = tier
        save_state(state)

        print(f"\n{'═' * 50}")
        print(f"  ITERATION {iteration}/{MAX_ITERATIONS}")
        print(f"  Tier: {tier} | Scope: {scope} | Focus: {state['focus']}")
        print(f"{'═' * 50}")

        # Step 1: Regression gate
        if not run_regression():
            print("\n✘ REGRESSION FAILURE — stopping loop")
            print("  Fix the regression before continuing.")
            state["history"].append({
                "iteration": iteration,
                "date": datetime.now().isoformat(),
                "result": "regression_failure",
            })
            save_state(state)
            return False

        # Step 2: Production test
        metrics = run_production_test()
        if metrics is None:
            print("\n✘ Production test produced no report — stopping")
            return False

        print("\n  Current metrics:")
        print_metrics(metrics)

        # Step 3: Check targets
        passed, failures = check_targets(metrics, tier)

        # Track best results
        dark_m = metrics.get("dark")
        light_m = metrics.get("light")
        if dark_m:
            if state["best_dark"] is None or dark_m["alpha_iou"] > state["best_dark"].get("alpha_iou", 0):
                state["best_dark"] = dark_m
        if light_m:
            if state["best_light"] is None or light_m["alpha_iou"] > state["best_light"].get("alpha_iou", 0):
                state["best_light"] = light_m

        if passed:
            print("\n✔ ALL TARGETS MET — production quality achieved!")
            state["history"].append({
                "iteration": iteration,
                "date": datetime.now().isoformat(),
                "result": "success",
                "metrics": metrics,
            })
            save_state(state)
            return True

        # Check for improvement
        prev_metrics = state["history"][-1].get("metrics") if state["history"] else None
        improved = False
        if prev_metrics and dark_m and prev_metrics.get("dark"):
            if dark_m["alpha_iou"] > prev_metrics["dark"].get("alpha_iou", 0):
                improved = True

        if improved:
            no_improvement_count = 0
        else:
            no_improvement_count += 1

        if no_improvement_count >= PLATEAU_TRIGGER and scope != "structural":
            print(f"\n  ⚠ No improvement for {PLATEAU_TRIGGER} iterations — escalating early")

        # Log iteration
        state["history"].append({
            "iteration": iteration,
            "date": datetime.now().isoformat(),
            "tier": tier,
            "scope": scope,
            "focus": state["focus"],
            "result": "needs_improvement",
            "failures": failures,
            "metrics": metrics,
            "improved": improved,
        })

        # Step 4: Print what needs fixing
        print(f"\n  Failures at tier {tier}:")
        for f in failures:
            print(f"    - {f}")
        print(f"\n  Scope: {scope}")
        print(f"  Agent should make ONE targeted change to app.js")
        print(f"  Focus on: {state['focus']} background extraction")
        print(f"\n  ⏸  Waiting for fix agent (iteration {iteration})...")
        print(f"  Run the fix, then restart this script to continue.")

        state["current_iteration"] = iteration + 1
        save_state(state)

        # In automated mode, we'd dispatch an agent here.
        # For now, stop and let the user/agent make the fix.
        return False

    print(f"\n✘ Max iterations ({MAX_ITERATIONS}) reached")
    print("  Best metrics achieved:")
    if state["best_dark"]:
        print(f"  Dark: IoU={state['best_dark']['alpha_iou']:.4f}")
    if state["best_light"]:
        print(f"  Light: IoU={state['best_light']['alpha_iou']:.4f}")
    save_state(state)
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
