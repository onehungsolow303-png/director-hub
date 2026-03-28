"""
Test light background presets via REST API.
Tests: light-balanced, light-soft, light-hard (heuristic mode)
       light-balanced (ai-remove mode)
"""

import json
import time
import urllib.request
import urllib.error

API_BASE = "http://127.0.0.1:8080/api"

# Test matrix: (preset, mode, output_dir, min_transparent, max_semi, min_opaque)
TESTS = [
    ("light-balanced", "heuristic", "output/test_light_balanced", 50, 5, 30),
    ("light-soft",     "heuristic", "output/test_light_soft",     45, 8, 30),
    ("light-hard",     "heuristic", "output/test_light_hard",     55, 3, 30),
    ("light-balanced", "ai-remove", "output/test_light_ai",       None, None, None),
]

IMAGE = "input/UI2.1.png"
POLL_INTERVAL = 3
TIMEOUT = 60


def post_extract(image, preset, mode, output_dir):
    payload = json.dumps({
        "image": image,
        "preset": preset,
        "mode": mode,
        "output_dir": output_dir,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/extract",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_status(job_id):
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > TIMEOUT:
            return None, elapsed
        req = urllib.request.Request(f"{API_BASE}/status/{job_id}")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        status = data.get("status")
        if status in ("completed", "failed"):
            return data, elapsed
        time.sleep(POLL_INTERVAL)


def check_thresholds(alpha_stats, min_transparent, max_semi, min_opaque):
    results = {}
    tp = alpha_stats.get("pct_transparent", 0)
    sp = alpha_stats.get("pct_semi", 0)
    op = alpha_stats.get("pct_opaque", 0)

    if min_transparent is not None:
        results["transparent >= {}%".format(min_transparent)] = tp >= min_transparent
    if max_semi is not None:
        results["semi <= {}%".format(max_semi)] = sp <= max_semi
    if min_opaque is not None:
        results["opaque >= {}%".format(min_opaque)] = op >= min_opaque
    return results


def main():
    rows = []

    for preset, mode, output_dir, min_t, max_s, min_o in TESTS:
        label = f"{preset} ({mode})"
        print(f"\n--- {label} ---")

        # Submit job
        try:
            resp = post_extract(IMAGE, preset, mode, output_dir)
        except Exception as e:
            print(f"  POST failed: {e}")
            rows.append((preset, mode, "POST_FAILED", "-", "-", "-", "-", {}, False))
            continue

        job_id = resp.get("job_id") or resp.get("id")
        if not job_id:
            print(f"  No job_id in response: {resp}")
            rows.append((preset, mode, "NO_JOB_ID", "-", "-", "-", "-", {}, False))
            continue
        print(f"  job_id: {job_id}")

        # Poll
        data, elapsed = poll_status(job_id)
        if data is None:
            print(f"  TIMEOUT after {elapsed:.1f}s")
            rows.append((preset, mode, "TIMEOUT", f"{elapsed:.1f}s", "-", "-", "-", {}, False))
            continue

        status = data.get("status")
        print(f"  status: {status}  elapsed: {elapsed:.1f}s")

        if status == "failed":
            err = data.get("error", "unknown")
            print(f"  error: {err}")
            rows.append((preset, mode, "failed", f"{elapsed:.1f}s", "-", "-", "-", {}, False))
            continue

        # Extract alpha stats — nested under results.alpha_stats.result
        results = data.get("results") or data.get("result") or {}
        alpha_stats_all = results.get("alpha_stats", {})
        alpha_stats = alpha_stats_all.get("result", {})
        tp = alpha_stats.get("pct_transparent", 0)
        sp = alpha_stats.get("pct_semi", 0)
        op = alpha_stats.get("pct_opaque", 0)
        print(f"  alpha: transparent={tp:.1f}% semi={sp:.1f}% opaque={op:.1f}%")

        # Threshold checks
        checks = check_thresholds(alpha_stats, min_t, max_s, min_o)
        overall = all(checks.values()) if checks else True
        for name, passed in checks.items():
            tag = "PASS" if passed else "FAIL"
            print(f"  {tag}: {name}")

        rows.append((preset, mode, status, f"{elapsed:.1f}s", tp, sp, op, checks, overall))

    # Summary table
    print("\n" + "=" * 110)
    print(f"{'Preset':<20} {'Mode':<12} {'Status':<12} {'Time':<8} {'Trans%':<8} {'Semi%':<8} {'Opaq%':<8} {'Checks':<30} {'Overall'}")
    print("-" * 110)
    for preset, mode, status, elapsed, tp, sp, op, checks, overall in rows:
        tp_s = f"{tp:.1f}" if isinstance(tp, (int, float)) else tp
        sp_s = f"{sp:.1f}" if isinstance(sp, (int, float)) else sp
        op_s = f"{op:.1f}" if isinstance(op, (int, float)) else op

        if checks:
            check_str = " | ".join(
                f"{'P' if v else 'F'}:{k.split()[0]}" for k, v in checks.items()
            )
        else:
            check_str = "n/a" if status == "completed" else "-"

        ov = "PASS" if overall else "FAIL"
        if status not in ("completed",):
            ov = "FAIL"

        print(f"{preset:<20} {mode:<12} {status:<12} {elapsed:<8} {tp_s:<8} {sp_s:<8} {op_s:<8} {check_str:<30} {ov}")

    print("=" * 110)

    # Final verdict
    all_pass = all(r[8] and r[2] == "completed" for r in rows)
    print(f"\nFinal verdict: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    exit(main())
