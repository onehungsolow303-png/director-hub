"""
Test dark background presets via the REST API.
Uses only stdlib: urllib.request, json, time.
"""

import json
import time
import urllib.request
import urllib.error
import sys

API_BASE = "http://127.0.0.1:8080/api"
TEST_IMAGE = r"C:\Pictures\Screenshots 1\Screenshot 2026-03-27 201511.png"
POLL_INTERVAL = 3   # seconds
TIMEOUT = 120       # seconds

# ── test definitions ────────────────────────────────────────────────
TESTS = [
    {
        "label": "dark-balanced / ai-remove",
        "payload": {
            "image": TEST_IMAGE,
            "preset": "dark-balanced",
            "mode": "ai-remove",
            "output_dir": "output/test_dark_dark-balanced",
        },
        "thresholds": {
            "min_transparent": 60,
            "max_semi": 5,
            "min_opaque": 15,
        },
    },
    {
        "label": "dark-soft / ai-remove",
        "payload": {
            "image": TEST_IMAGE,
            "preset": "dark-soft",
            "mode": "ai-remove",
            "output_dir": "output/test_dark_dark-soft",
        },
        "thresholds": {
            "min_transparent": 55,
            "max_semi": 8,
            "min_opaque": 15,
        },
    },
    {
        "label": "dark-hard / ai-remove",
        "payload": {
            "image": TEST_IMAGE,
            "preset": "dark-hard",
            "mode": "ai-remove",
            "output_dir": "output/test_dark_dark-hard",
        },
        "thresholds": {
            "min_transparent": 65,
            "max_semi": 3,
            "min_opaque": 15,
        },
    },
    {
        "label": "dark-balanced / heuristic",
        "payload": {
            "image": TEST_IMAGE,
            "preset": "dark-balanced",
            "mode": "heuristic",
            "output_dir": "output/test_dark_heuristic",
        },
        "thresholds": {
            "min_transparent": 60,
            "max_semi": 5,
            "min_opaque": 15,
        },
    },
]


# ── helpers ─────────────────────────────────────────────────────────
def api_post(path, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get(path):
    req = urllib.request.Request(f"{API_BASE}{path}", method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_until_done(job_id):
    """Poll status endpoint; return (status_obj, elapsed_seconds)."""
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > TIMEOUT:
            return {"status": "timeout"}, elapsed
        status = api_get(f"/status/{job_id}")
        st = status.get("status", "unknown")
        if st in ("completed", "failed", "error"):
            return status, elapsed
        time.sleep(POLL_INTERVAL)


def check_thresholds(alpha_stats, thresholds):
    """Return dict of {check_name: (pass_bool, actual, required)}."""
    results = {}
    # alpha_stats may be nested: { "result": { "pct_transparent": ... } }
    # or flat: { "transparent": ..., "pct_transparent": ... }
    stats = alpha_stats
    if "result" in alpha_stats and isinstance(alpha_stats["result"], dict):
        stats = alpha_stats["result"]

    transparent = stats.get("pct_transparent", stats.get("transparent", 0))
    semi = stats.get("pct_semi", stats.get("semi_transparent", stats.get("semi", 0)))
    opaque = stats.get("pct_opaque", stats.get("opaque", 0))

    results["min_transparent"] = (
        transparent >= thresholds["min_transparent"],
        transparent,
        f">= {thresholds['min_transparent']}%",
    )
    results["max_semi"] = (
        semi <= thresholds["max_semi"],
        semi,
        f"<= {thresholds['max_semi']}%",
    )
    results["min_opaque"] = (
        opaque >= thresholds["min_opaque"],
        opaque,
        f">= {thresholds['min_opaque']}%",
    )
    return results


# ── main ────────────────────────────────────────────────────────────
def main():
    rows = []  # collect for summary

    for test in TESTS:
        label = test["label"]
        print(f"\n{'='*60}")
        print(f"  TEST: {label}")
        print(f"{'='*60}")

        # 1. submit job
        try:
            resp = api_post("/extract", test["payload"])
        except urllib.error.URLError as e:
            print(f"  ERROR submitting job: {e}")
            rows.append({
                "label": label,
                "status": "submit_error",
                "elapsed": 0,
                "alpha": {},
                "checks": {},
                "overall": "FAIL",
                "error": str(e),
            })
            continue

        job_id = resp.get("id") or resp.get("job_id")
        if not job_id:
            print(f"  ERROR: no job id in response: {resp}")
            rows.append({
                "label": label,
                "status": "no_job_id",
                "elapsed": 0,
                "alpha": {},
                "checks": {},
                "overall": "FAIL",
                "error": f"Response: {resp}",
            })
            continue

        print(f"  Job ID: {job_id}")

        # 2. poll
        status_obj, elapsed = poll_until_done(job_id)
        st = status_obj.get("status", "unknown")
        print(f"  Status: {st}  ({elapsed:.1f}s)")

        if st != "completed":
            err = status_obj.get("error", status_obj.get("message", ""))
            print(f"  Error detail: {err}")
            rows.append({
                "label": label,
                "status": st,
                "elapsed": elapsed,
                "alpha": {},
                "checks": {},
                "overall": "FAIL",
                "error": str(err),
            })
            continue

        # 3. alpha stats
        results = status_obj.get("results", status_obj.get("result", {}))
        alpha = results.get("alpha_stats", {})
        print(f"  Alpha stats: {json.dumps(alpha, indent=2)}")

        # 4. threshold checks
        checks = check_thresholds(alpha, test["thresholds"])
        overall = "PASS" if all(c[0] for c in checks.values()) else "FAIL"

        for name, (ok, actual, req) in checks.items():
            tag = "PASS" if ok else "FAIL"
            print(f"    {name}: {actual}% {req} -> {tag}")
        print(f"  Overall: {overall}")

        rows.append({
            "label": label,
            "status": st,
            "elapsed": elapsed,
            "alpha": alpha,
            "checks": checks,
            "overall": overall,
            "error": "",
        })

    # ── summary table ───────────────────────────────────────────────
    print(f"\n\n{'='*100}")
    print("  SUMMARY")
    print(f"{'='*100}")

    hdr = (
        f"{'Preset / Mode':<30} {'Status':<12} {'Time':>6} "
        f"{'Trans%':>7} {'Semi%':>6} {'Opaq%':>6} "
        f"{'MinTrans':>9} {'MaxSemi':>8} {'MinOpaq':>8} {'Result':>8}"
    )
    print(hdr)
    print("-" * len(hdr))

    for r in rows:
        a = r["alpha"]
        # Handle nested alpha_stats structure
        s = a.get("result", a) if isinstance(a.get("result"), dict) else a
        tr = s.get("pct_transparent", s.get("transparent", "-"))
        se = s.get("pct_semi", s.get("semi_transparent", s.get("semi", "-")))
        op = s.get("pct_opaque", s.get("opaque", "-"))

        c = r["checks"]
        ct = "PASS" if c.get("min_transparent", (False,))[0] else "FAIL" if c else "-"
        cs = "PASS" if c.get("max_semi", (False,))[0] else "FAIL" if c else "-"
        co = "PASS" if c.get("min_opaque", (False,))[0] else "FAIL" if c else "-"

        print(
            f"{r['label']:<30} {r['status']:<12} {r['elapsed']:>5.1f}s "
            f"{str(tr):>7} {str(se):>6} {str(op):>6} "
            f"{ct:>9} {cs:>8} {co:>8} {r['overall']:>8}"
        )

    print()
    all_pass = all(r["overall"] == "PASS" for r in rows)
    print(f"  FINAL VERDICT: {'ALL PASS' if all_pass else 'SOME FAILURES'}")

    # print failure details
    failures = [r for r in rows if r["overall"] != "PASS"]
    if failures:
        print(f"\n  Failed tests ({len(failures)}):")
        for r in failures:
            print(f"    - {r['label']}: status={r['status']}")
            if r.get("error"):
                print(f"      error: {r['error']}")
            for name, (ok, actual, req) in r.get("checks", {}).items():
                if not ok:
                    print(f"      {name}: got {actual}%, needed {req}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
