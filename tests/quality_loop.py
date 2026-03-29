"""Autonomous Quality Improvement Loop — Orchestrator.

Drives the test -> analyze -> modify -> retest cycle.
Two phases: parameter tuning (P1, max 10 iter) then structural code (P2, max 5 iter).
Branch-per-attempt: main only receives cherry-picked improvements.

Usage:
    .venv/Scripts/python.exe tests/quality_loop.py
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Dev\Image generator")
REPORTS_DIR = ROOT / "tests" / "reports"
HISTORY_PATH = REPORTS_DIR / "iteration_history.json"
QUALITY_REPORT = REPORTS_DIR / "quality_report.json"
WHAT_WORKED = ROOT / ".claude" / "rules" / "what-worked.md"

# ── Targets ───────────────────────────────────────────────────────────

TARGETS = {
    "dark_alpha_iou": 0.99,
    "light_alpha_iou": 0.998,
    "dark_alpha_mae": 2.0,
    "light_alpha_mae": 0.3,
    "dark_ssim": 0.20,
    "light_ssim": 0.50,
}

PHASE1_MAX = 10
PHASE2_MAX = 5
PLATEAU_TRIGGER = 3


# ── Helpers ───────────────────────────────────────────────────────────

def run_test_suite() -> dict:
    """Run the full pytest suite and return metrics from quality_report.json."""
    print("  Running test suite...")
    result = subprocess.run(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "pytest",
         "tests/test_smoke.py", "tests/test_unit_metrics.py",
         "tests/test_live_extraction.py", "tests/test_quality_gates.py",
         "-v", "--tb=short"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    print(f"  Test suite exit code: {result.returncode}")

    if QUALITY_REPORT.exists():
        with open(QUALITY_REPORT) as f:
            return json.load(f)
    return {}


def extract_metrics(report: dict) -> dict:
    """Extract key metrics from quality_report.json."""
    metrics = {}

    dark_iou, dark_mae, dark_ssim = [], [], []
    for key, data in report.items():
        if key.startswith("dark-"):
            m = data.get("metrics", {})
            if "alpha_iou" in m:
                dark_iou.append(m["alpha_iou"])
            if "alpha_mae" in m:
                dark_mae.append(m["alpha_mae"])
            if "ssim" in m:
                dark_ssim.append(m["ssim"])

    light_iou, light_mae, light_ssim = [], [], []
    for key, data in report.items():
        if key.startswith("light-"):
            m = data.get("metrics", {})
            if "alpha_iou" in m:
                light_iou.append(m["alpha_iou"])
            if "alpha_mae" in m:
                light_mae.append(m["alpha_mae"])
            if "ssim" in m:
                light_ssim.append(m["ssim"])

    metrics["dark_alpha_iou"] = sum(dark_iou) / len(dark_iou) if dark_iou else 0
    metrics["dark_alpha_mae"] = sum(dark_mae) / len(dark_mae) if dark_mae else 999
    metrics["dark_ssim"] = sum(dark_ssim) / len(dark_ssim) if dark_ssim else 0
    metrics["light_alpha_iou"] = sum(light_iou) / len(light_iou) if light_iou else 0
    metrics["light_alpha_mae"] = sum(light_mae) / len(light_mae) if light_mae else 999
    metrics["light_ssim"] = sum(light_ssim) / len(light_ssim) if light_ssim else 0

    return metrics


def targets_met(metrics: dict) -> bool:
    """Check if all quality targets are met."""
    for key, target in TARGETS.items():
        val = metrics.get(key, 0)
        if "mae" in key:
            if val > target:
                return False
        else:
            if val < target:
                return False
    return True


def avg_alpha_iou(metrics: dict) -> float:
    """Average of dark and light Alpha IoU."""
    return (metrics.get("dark_alpha_iou", 0) + metrics.get("light_alpha_iou", 0)) / 2


def git_branch(name: str):
    """Create and checkout a new branch."""
    subprocess.run(["git", "checkout", "-b", name], cwd=str(ROOT), capture_output=True)


def git_checkout_main():
    """Checkout main branch."""
    subprocess.run(["git", "checkout", "master"], cwd=str(ROOT), capture_output=True)


def git_cherry_pick(branch: str):
    """Cherry-pick the latest commit from a branch onto current branch."""
    result = subprocess.run(
        ["git", "log", branch, "-1", "--format=%H"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    commit = result.stdout.strip()
    if commit:
        subprocess.run(["git", "cherry-pick", commit], cwd=str(ROOT), capture_output=True)


def load_history() -> dict:
    """Load iteration history or create new."""
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH) as f:
            return json.load(f)
    return {
        "baseline": {},
        "targets": TARGETS,
        "iterations": [],
        "best_so_far": {},
    }


def save_history(history: dict):
    """Save iteration history."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)


def append_what_worked(entry: str):
    """Append an iteration log entry to what-worked.md."""
    with open(WHAT_WORKED, "a") as f:
        f.write("\n" + entry + "\n")


def format_iteration_log(iteration: dict) -> str:
    """Format a what-worked.md entry for an iteration."""
    phase = "P1" if iteration["phase"] == 1 else "P2"
    idx = iteration["index"]
    param = iteration.get("parameter", iteration.get("description", "unknown"))
    date = iteration.get("date", datetime.now().strftime("%Y-%m-%d"))

    lines = [f"### Iteration {phase}-{idx}: {param} ({date})"]

    if "old_value" in iteration:
        lines.append(f"- **Changed**: {iteration.get('parameter', '?')} "
                      f"{iteration['old_value']} -> {iteration['new_value']}")
    if "hypothesis" in iteration:
        lines.append(f"- **Hypothesis**: {iteration['hypothesis']}")

    mb = iteration.get("metrics_before", {})
    ma = iteration.get("metrics_after", {})
    for key in ["dark_alpha_iou", "light_alpha_iou", "dark_ssim", "light_ssim"]:
        before = mb.get(key, "?")
        after = ma.get(key, "?")
        if isinstance(before, float) and isinstance(after, float):
            delta = after - before
            sign = "+" if delta >= 0 else ""
            lines.append(f"- **{key}**: {before:.4f} -> {after:.4f} ({sign}{delta:.4f})")

    improved = iteration.get("improved", False)
    kept = iteration.get("kept", False)
    result = "IMPROVEMENT" if improved else "NO CHANGE / REGRESSION"
    lines.append(f"- **Result**: {result}")
    lines.append(f"- **Keep**: {'YES (cherry-picked)' if kept else 'NO (branch abandoned)'}")
    lines.append(f"- **Branch**: {iteration.get('branch', '?')}")

    return "\n".join(lines)


def print_summary(history: dict, start_metrics: dict, end_metrics: dict):
    """Print final summary."""
    total = len(history["iterations"])
    kept = sum(1 for i in history["iterations"] if i.get("kept"))
    abandoned = total - kept

    print("\n" + "=" * 80)
    print("  QUALITY LOOP — FINAL SUMMARY")
    print("=" * 80)
    print(f"  Total iterations: {total} (kept: {kept}, abandoned: {abandoned})")
    print()
    print(f"  {'Metric':<20} {'Start':>10} {'End':>10} {'Target':>10} {'Gap':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for key, target in TARGETS.items():
        start = start_metrics.get(key, 0)
        end = end_metrics.get(key, 0)
        gap = target - end if "mae" not in key else end - target
        print(f"  {key:<20} {start:>10.4f} {end:>10.4f} {target:>10.4f} {gap:>+10.4f}")

    met = targets_met(end_metrics)
    print()
    if met:
        print("  STATUS: ALL TARGETS MET")
    else:
        print("  STATUS: Targets not fully met. See iteration history for details.")
    print("=" * 80)


# ── Main Loop ─────────────────────────────────────────────────────────

def main():
    history = load_history()

    print("=" * 80)
    print("  QUALITY LOOP — Collecting baseline metrics")
    print("=" * 80)
    report = run_test_suite()
    baseline = extract_metrics(report)
    history["baseline"] = baseline
    history["best_so_far"] = baseline.copy()
    save_history(history)

    print(f"\n  Baseline: dark_aIoU={baseline.get('dark_alpha_iou', 0):.4f}  "
          f"light_aIoU={baseline.get('light_alpha_iou', 0):.4f}")

    if targets_met(baseline):
        print("\n  All targets already met! Nothing to do.")
        return 0

    start_metrics = baseline.copy()
    current_metrics = baseline.copy()
    no_improvement_streak = 0

    for i in range(1, PHASE1_MAX + 1):
        print(f"\n{'=' * 80}")
        print(f"  PHASE 1 — Iteration {i}/{PHASE1_MAX}")
        print(f"{'=' * 80}")

        if targets_met(current_metrics):
            print("  Targets met!")
            break

        if no_improvement_streak >= PLATEAU_TRIGGER:
            print(f"  Plateau detected ({no_improvement_streak} consecutive no-improvement). Escalating to Phase 2.")
            break

        branch_name = f"iter/p1-{i:02d}"
        print(f"  Branch: {branch_name}")

        print(f"\n  --- AGENT DISPATCH POINT ---")
        print(f"  Master should now:")
        print(f"    1. Dispatch research-advisor with current metrics")
        print(f"    2. Get parameter recommendation")
        print(f"    3. Create branch: git checkout -b {branch_name}")
        print(f"    4. Dispatch extraction-analyst to modify ONE parameter")
        print(f"    5. Run test suite")
        print(f"    6. Dispatch quality-checker to compare")
        print(f"    7. Cherry-pick or abandon")
        print(f"  Current best: dark_aIoU={current_metrics.get('dark_alpha_iou', 0):.4f}  "
              f"light_aIoU={current_metrics.get('light_alpha_iou', 0):.4f}")
        print(f"  Target: dark_aIoU>={TARGETS['dark_alpha_iou']}  "
              f"light_aIoU>={TARGETS['light_alpha_iou']}")
        print(f"  Plateau counter: {no_improvement_streak}/{PLATEAU_TRIGGER}")

        iteration = {
            "id": f"p1-{i:02d}",
            "phase": 1,
            "index": i,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "metrics_before": current_metrics.copy(),
            "branch": branch_name,
            "status": "awaiting_agent_dispatch",
        }
        history["iterations"].append(iteration)
        save_history(history)

        print(f"\n  Orchestrator framework ready. Agents should drive iterations from here.")
        print(f"  Run with CEO agent for autonomous execution.")
        break

    print_summary(history, start_metrics, current_metrics)
    save_history(history)
    return 0


if __name__ == "__main__":
    sys.exit(main())
