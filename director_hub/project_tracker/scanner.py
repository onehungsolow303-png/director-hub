"""Collect project-state snapshots from the repos + runtime services.

Each function returns a plain dict. Keeping them separate makes it easy to
test each in isolation and easy to extend (e.g. add test-status scanner
later without touching git scanner).
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

REPOS: dict[str, Path] = {
    "forever_engine": Path("C:/Dev/Forever engine"),
    "asset_manager": Path("C:/Dev/Asset Manager"),
    "director_hub": Path("C:/Dev/Director Hub"),
    "shared": Path("C:/Dev/.shared"),
}

# File patterns worth surfacing as "recently modified" per repo.
SOURCE_GLOBS: dict[str, tuple[str, ...]] = {
    "forever_engine": ("Assets/Scripts/**/*.cs",),
    "asset_manager": ("asset_manager/**/*.py",),
    "director_hub": ("director_hub/**/*.py",),
    "shared": ("schemas/*.json", "docs/**/*.md"),
}

SERVICES = {
    "asset_manager": "http://127.0.0.1:7801/health",
    "director_hub": "http://127.0.0.1:7802/health",
    "game_state_server": "http://127.0.0.1:7803/",
}

UNITY_BUILD_LOG = Path("C:/Dev/unity_build.log")
MEMORY_DIR = Path.home() / ".claude" / "projects" / "C--Dev" / "memory"
HISTORY_JSONL = Path.home() / ".claude" / "history.jsonl"
TRANSCRIPT_DIR = Path.home() / ".claude" / "projects" / "C--Dev"
CLAUDE_MEM_DB = Path.home() / ".claude-mem" / "claude-mem.db"


def _git(repo: Path, *args: str) -> str:
    """Run a git command in `repo`, return stdout stripped. Empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def scan_git(repo: Path) -> dict[str, Any]:
    """Branch, HEAD, recent commits, dirty-count for one repo."""
    if not (repo / ".git").exists():
        return {"available": False}

    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    head_line = _git(repo, "log", "-1", "--format=%H|%s|%cI|%an")
    head: dict[str, str] = {}
    if head_line:
        parts = head_line.split("|", 3)
        if len(parts) == 4:
            head = {
                "hash": parts[0][:8],
                "subject": parts[1],
                "timestamp": parts[2],
                "author": parts[3],
            }

    log_text = _git(repo, "log", "-20", "--format=%h|%s|%cI")
    recent_commits = []
    for line in log_text.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            recent_commits.append({"hash": parts[0], "subject": parts[1], "timestamp": parts[2]})

    status = _git(repo, "status", "--porcelain")
    staged = unstaged = untracked = 0
    for line in status.splitlines():
        if not line:
            continue
        x, y = line[0], line[1]
        if line.startswith("??"):
            untracked += 1
        else:
            if x != " ":
                staged += 1
            if y != " ":
                unstaged += 1

    return {
        "available": True,
        "branch": branch,
        "head": head,
        "recent_commits": recent_commits,
        "dirty": {"staged": staged, "unstaged": unstaged, "untracked": untracked},
    }


def scan_recently_modified(
    repo: Path, globs: tuple[str, ...], limit: int = 10
) -> list[dict[str, Any]]:
    """Top N most-recently-modified files matching any glob."""
    if not repo.exists():
        return []
    matches: list[tuple[float, Path]] = []
    for pat in globs:
        for p in repo.glob(pat):
            try:
                matches.append((p.stat().st_mtime, p))
            except OSError:
                continue
    matches.sort(reverse=True)
    result = []
    for mtime, p in matches[:limit]:
        rel = p.relative_to(repo).as_posix()
        result.append(
            {
                "path": rel,
                "mtime": datetime.fromtimestamp(mtime, tz=UTC).isoformat(),
            }
        )
    return result


def scan_services() -> dict[str, Any]:
    """HEAD-ping all known service health endpoints. 2s timeout each."""
    out: dict[str, Any] = {}
    for name, url in SERVICES.items():
        try:
            resp = httpx.get(url, timeout=2.0)
            out[name] = {
                "url": url,
                "ok": resp.status_code < 500,
                "status": resp.status_code,
                "checked_at": datetime.now(tz=UTC).isoformat(),
            }
        except httpx.HTTPError:
            out[name] = {
                "url": url,
                "ok": False,
                "status": None,
                "checked_at": datetime.now(tz=UTC).isoformat(),
            }
    return out


def scan_unity_build() -> dict[str, Any]:
    """Read last Unity build result from the well-known log location."""
    if not UNITY_BUILD_LOG.exists():
        return {"available": False}
    try:
        text = UNITY_BUILD_LOG.read_text(errors="ignore")
    except OSError:
        return {"available": False}
    mtime = datetime.fromtimestamp(UNITY_BUILD_LOG.stat().st_mtime, tz=UTC)
    result = "unknown"
    size_mb: int | None = None
    for line in text.splitlines():
        if "Build succeeded" in line:
            result = "succeeded"
            # "[StandaloneBuild] Build succeeded! Size: 2221 MB"
            parts = line.split("Size:")
            if len(parts) == 2:
                try:
                    size_mb = int(parts[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
        elif "Build failed" in line or "Build Finished, Result: Failure" in line:
            result = "failed"
    return {"available": True, "at": mtime.isoformat(), "result": result, "size_mb": size_mb}


def scan_memory() -> dict[str, Any]:
    """Survey the MEMORY.md index and list the referenced session docs."""
    if not MEMORY_DIR.exists():
        return {"available": False, "dir": str(MEMORY_DIR)}
    index = MEMORY_DIR / "MEMORY.md"
    if not index.exists():
        return {"available": True, "dir": str(MEMORY_DIR), "memory_md": None}
    memory_md_mtime = datetime.fromtimestamp(index.stat().st_mtime, tz=UTC).isoformat()

    session_docs = []
    for p in MEMORY_DIR.glob("project_session_*.md"):
        session_docs.append(
            {
                "name": p.name,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat(),
            }
        )
    session_docs.sort(key=lambda d: d["mtime"], reverse=True)

    return {
        "available": True,
        "dir": str(MEMORY_DIR),
        "memory_md_mtime": memory_md_mtime,
        "session_docs": session_docs[:10],
        "latest_session_doc": session_docs[0]["name"] if session_docs else None,
    }


def scan_tests() -> dict[str, Any]:
    """Cached test counts. Run `pytest --co -q` would be ideal but too slow for 15-min cadence;
    instead we read a sidecar file if present (see state/last_test_run.json).
    For v1, just count `test_*.py` files per Python repo as a proxy."""
    out: dict[str, Any] = {}
    for name, repo in REPOS.items():
        if name not in ("asset_manager", "director_hub"):
            continue
        tests_dir = repo / "tests"
        if tests_dir.exists():
            out[name] = {
                "test_file_count": len(list(tests_dir.rglob("test_*.py"))),
                "last_test_run": None,  # populated once a pytest plugin writes it
            }
    return out


def scan_transcripts(project_filter: str = "C:\\Dev") -> dict[str, Any]:
    """Read Claude Code history.jsonl + session file inventory for this project."""
    if not HISTORY_JSONL.exists():
        return {"available": False}

    # Parse history.jsonl — one JSON object per line
    recent_prompts: list[dict[str, Any]] = []
    total_prompts = 0
    try:
        with HISTORY_JSONL.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("project") != project_filter:
                    continue
                total_prompts += 1
                recent_prompts.append(
                    {
                        "display": (entry.get("display") or "")[:120],
                        "timestamp": datetime.fromtimestamp(
                            entry.get("timestamp", 0) / 1000, tz=UTC
                        ).isoformat(),
                        "session_id": entry.get("sessionId", ""),
                    }
                )
    except OSError:
        return {"available": False}

    # Keep last 20 (newest first) — file is chronological so take tail
    recent_prompts = recent_prompts[-20:]
    recent_prompts.reverse()

    # Session file inventory
    session_files: list[dict[str, Any]] = []
    total_size = 0
    if TRANSCRIPT_DIR.exists():
        for p in TRANSCRIPT_DIR.glob("*.jsonl"):
            try:
                st = p.stat()
                total_size += st.st_size
                session_files.append(
                    {
                        "name": p.name,
                        "mtime": datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
                        "size_bytes": st.st_size,
                    }
                )
            except OSError:
                continue
    session_files.sort(key=lambda d: d["mtime"], reverse=True)

    return {
        "available": True,
        "history_file": str(HISTORY_JSONL),
        "total_prompts": total_prompts,
        "recent_prompts": recent_prompts,
        "session_files": {
            "count": len(session_files),
            "total_size_bytes": total_size,
            "recent": session_files[:5],
        },
    }


def scan_claude_mem(
    project_filter: tuple[str, ...] = ("Dev", "C--Dev"),
) -> dict[str, Any]:
    """Read claude-mem SQLite DB (read-only) for session summaries, observations, prompts."""
    if not CLAUDE_MEM_DB.exists():
        return {"available": False}

    db_uri = f"file:{CLAUDE_MEM_DB.as_posix()}?mode=ro"
    try:
        con = sqlite3.connect(db_uri, uri=True, timeout=5)
        con.row_factory = sqlite3.Row
    except sqlite3.Error:
        return {"available": False, "db_path": str(CLAUDE_MEM_DB)}

    placeholders = ",".join("?" for _ in project_filter)

    try:
        cur = con.cursor()

        # Last 3 session summaries
        cur.execute(
            f"SELECT request, investigated, learned, completed, next_steps, created_at "
            f"FROM session_summaries WHERE project IN ({placeholders}) "
            f"ORDER BY created_at_epoch DESC LIMIT 3",
            project_filter,
        )
        session_summaries = [
            {
                "request": r["request"] or "",
                "investigated": (r["investigated"] or "")[:500],
                "learned": (r["learned"] or "")[:500],
                "completed": (r["completed"] or "")[:500],
                "next_steps": (r["next_steps"] or "")[:300],
                "created_at": r["created_at"] or "",
            }
            for r in cur.fetchall()
        ]

        # Last 10 observations
        cur.execute(
            f"SELECT type, title, subtitle, created_at "
            f"FROM observations WHERE project IN ({placeholders}) "
            f"ORDER BY created_at_epoch DESC LIMIT 10",
            project_filter,
        )
        observations = [
            {
                "type": r["type"] or "",
                "title": r["title"] or "",
                "subtitle": (r["subtitle"] or "")[:200],
                "created_at": r["created_at"] or "",
            }
            for r in cur.fetchall()
        ]

        # Last 20 user prompts
        cur.execute(
            f"SELECT prompt_text, created_at "
            f"FROM user_prompts WHERE content_session_id IN "
            f"(SELECT content_session_id FROM sdk_sessions WHERE project IN ({placeholders})) "
            f"ORDER BY created_at_epoch DESC LIMIT 20",
            project_filter,
        )
        recent_prompts = [
            {
                "prompt_text": (r["prompt_text"] or "")[:120],
                "created_at": r["created_at"] or "",
            }
            for r in cur.fetchall()
        ]
    except sqlite3.Error:
        con.close()
        return {"available": False, "db_path": str(CLAUDE_MEM_DB)}
    finally:
        con.close()

    return {
        "available": True,
        "db_path": str(CLAUDE_MEM_DB),
        "session_summaries": session_summaries,
        "observations": observations,
        "recent_prompts": recent_prompts,
    }


def full_scan() -> dict[str, Any]:
    """One full project-state snapshot. ~1-2 seconds wall clock."""
    started = time.monotonic()
    snapshot: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "repos": {},
        "services": scan_services(),
        "tests": scan_tests(),
        "memory": scan_memory(),
        "transcripts": scan_transcripts(),
        "claude_mem": scan_claude_mem(),
        "builds": {"last_unity_build": scan_unity_build()},
    }
    for name, repo in REPOS.items():
        git_state = scan_git(repo)
        snapshot["repos"][name] = {
            "path": str(repo),
            **git_state,
            "recently_modified": scan_recently_modified(repo, SOURCE_GLOBS.get(name, ())),
        }
    snapshot["scan_elapsed_ms"] = int((time.monotonic() - started) * 1000)
    return snapshot
