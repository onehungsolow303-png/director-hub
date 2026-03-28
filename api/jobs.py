"""Thread-safe job manager for tracking async API jobs."""

import threading
import time
from typing import Any, Dict, Optional


class JobManager:
    """Manages async job lifecycle with thread-safe operations."""

    def __init__(self, expiry_seconds: int = 3600):
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._counters: Dict[str, int] = {}
        self.expiry_seconds = expiry_seconds

    def _next_seq(self, job_type: str) -> int:
        self._counters[job_type] = self._counters.get(job_type, 0) + 1
        return self._counters[job_type]

    def create(self, job_type: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Create a new job and return its job_id."""
        with self._lock:
            ts = int(time.time())
            seq = self._next_seq(job_type)
            job_id = f"{job_type}_{ts}_{seq:03d}"
            self._jobs[job_id] = {
                "job_id": job_id,
                "job_type": job_type,
                "params": params or {},
                "status": "pending",
                "progress": 0,
                "step": None,
                "results": None,
                "error": None,
                "code": None,
                "created_at": ts,
                "started_at": None,
                "completed_at": None,
            }
            return job_id

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Return a copy of the job dict, or None if not found."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            elapsed_ms = None
            if job["started_at"] is not None:
                end = job["completed_at"] if job["completed_at"] is not None else time.time()
                elapsed_ms = int((end - job["started_at"]) * 1000)
            result = dict(job)
            result["elapsed_ms"] = elapsed_ms
            return result

    def update(self, job_id: str, **kwargs) -> bool:
        """Update job fields. Returns False if job not found."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            allowed = {"status", "progress", "step", "results", "error", "code"}
            for key, value in kwargs.items():
                if key in allowed:
                    job[key] = value
            # Auto-set timestamps based on status transitions
            status = job.get("status")
            if status == "processing" and job["started_at"] is None:
                job["started_at"] = time.time()
            if status in ("completed", "failed") and job["completed_at"] is None:
                job["completed_at"] = time.time()
                if job["started_at"] is None:
                    job["started_at"] = job["completed_at"]
            return True

    def cleanup(self) -> int:
        """Remove expired jobs. Returns count of removed jobs."""
        now = time.time()
        cutoff = now - self.expiry_seconds
        with self._lock:
            expired = [
                jid for jid, job in self._jobs.items()
                if job["created_at"] < cutoff
            ]
            for jid in expired:
                del self._jobs[jid]
            return len(expired)

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Return a shallow copy of all jobs."""
        with self._lock:
            return {jid: dict(job) for jid, job in self._jobs.items()}
