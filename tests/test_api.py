"""Unit tests for api/jobs.py — runs standalone without pytest."""

import sys
import os
import time

# Allow importing from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.jobs import JobManager


def test_create_job():
    mgr = JobManager()
    job_id = mgr.create("extract", {"file": "ui.png"})
    assert job_id.startswith("extract_"), f"Bad prefix: {job_id}"
    parts = job_id.split("_")
    assert len(parts) == 3, f"Expected 3 parts, got {parts}"
    assert parts[2] == "001", f"Expected seq 001, got {parts[2]}"
    job = mgr.get(job_id)
    assert job is not None
    assert job["status"] == "pending"
    assert job["progress"] == 0
    assert job["results"] is None
    assert job["elapsed_ms"] is None
    print("  PASS test_create_job")


def test_update_job_status():
    mgr = JobManager()
    job_id = mgr.create("extract", {})
    result = mgr.update(job_id, status="processing", progress=25, step="loading")
    assert result is True
    job = mgr.get(job_id)
    assert job["status"] == "processing"
    assert job["progress"] == 25
    assert job["step"] == "loading"
    assert job["started_at"] is not None, "started_at should be set when status=processing"
    assert job["elapsed_ms"] is not None, "elapsed_ms should be non-None once started"
    print("  PASS test_update_job_status")


def test_complete_job():
    mgr = JobManager()
    job_id = mgr.create("extract", {})
    mgr.update(job_id, status="processing")
    time.sleep(0.01)
    mgr.update(job_id, status="completed", progress=100, results={"output": "file.png"})
    job = mgr.get(job_id)
    assert job["status"] == "completed"
    assert job["results"] == {"output": "file.png"}
    assert job["completed_at"] is not None
    assert job["elapsed_ms"] >= 0
    print("  PASS test_complete_job")


def test_fail_job():
    mgr = JobManager()
    job_id = mgr.create("extract", {})
    mgr.update(job_id, status="processing")
    mgr.update(job_id, status="failed", error="ComfyUI timeout", code="TIMEOUT")
    job = mgr.get(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "ComfyUI timeout"
    assert job["code"] == "TIMEOUT"
    assert job["completed_at"] is not None
    print("  PASS test_fail_job")


def test_job_not_found():
    mgr = JobManager()
    result = mgr.get("nonexistent_123_001")
    assert result is None, f"Expected None, got {result}"
    update_result = mgr.update("nonexistent_123_001", status="processing")
    assert update_result is False, f"Expected False, got {update_result}"
    print("  PASS test_job_not_found")


def test_expire_old_jobs():
    mgr = JobManager(expiry_seconds=1)
    job_id = mgr.create("extract", {})
    assert mgr.get(job_id) is not None

    # Manually backdate created_at to simulate expiry
    with mgr._lock:
        mgr._jobs[job_id]["created_at"] = time.time() - 2

    removed = mgr.cleanup()
    assert removed == 1, f"Expected 1 removed, got {removed}"
    assert mgr.get(job_id) is None, "Job should be gone after cleanup"
    print("  PASS test_expire_old_jobs")


if __name__ == "__main__":
    tests = [
        test_create_job,
        test_update_job_status,
        test_complete_job,
        test_fail_job,
        test_job_not_found,
        test_expire_old_jobs,
    ]

    passed = 0
    failed = 0
    print(f"Running {len(tests)} tests...\n")
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"  FAIL {test.__name__}: {exc}")
            failed += 1

    print(f"\n{passed}/{len(tests)} tests passed", end="")
    if failed:
        print(f", {failed} FAILED")
        sys.exit(1)
    else:
        print()
