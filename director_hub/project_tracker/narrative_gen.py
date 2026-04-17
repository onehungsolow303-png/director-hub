"""Render a project-state snapshot as markdown.

The narrative is the primary consumption surface for new Claude Code
sessions — load this into context and you know where everything stands.
Format is terse structured bullet lists (one fact per line) to maximize
information density for Claude context injection.
"""

from __future__ import annotations

from typing import Any


def _fmt_dirty(dirty: dict[str, int]) -> str:
    s = dirty.get("staged", 0)
    u = dirty.get("unstaged", 0)
    un = dirty.get("untracked", 0)
    total = s + u + un
    if total == 0:
        return "clean"
    parts = []
    if s:
        parts.append(f"{s} staged")
    if u:
        parts.append(f"{u} unstaged")
    if un:
        parts.append(f"{un} untracked")
    return ", ".join(parts)


def render(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Project State — scanned by Director Hub")
    lines.append("")
    lines.append(f"**Generated:** {snapshot.get('generated_at', 'unknown')}")
    lines.append(f"**Scan elapsed:** {snapshot.get('scan_elapsed_ms', '?')}ms")
    lines.append("")

    # Repos
    lines.append("## Repos")
    lines.append("")
    for name, info in snapshot.get("repos", {}).items():
        if not info.get("available"):
            lines.append(f"- **{name}** — git not available at `{info.get('path')}`")
            continue
        head = info.get("head", {})
        lines.append(
            f"- **{name}** `{info.get('branch', '?')}` @ "
            f"`{head.get('hash', '?')}` — {head.get('subject', '?')} "
            f"_(dirty: {_fmt_dirty(info.get('dirty', {}))})_"
        )
    lines.append("")

    # Recent commits (across all repos, interleaved by time)
    lines.append("## Recent commits (most recent first, top 20 across all repos)")
    lines.append("")
    all_commits: list[tuple[str, str, str, str]] = []
    for name, info in snapshot.get("repos", {}).items():
        for c in info.get("recent_commits", []):
            all_commits.append(
                (c.get("timestamp", ""), name, c.get("hash", ""), c.get("subject", ""))
            )
    all_commits.sort(reverse=True)
    for _ts, repo, h, subj in all_commits[:20]:
        lines.append(f"- `{h}` **{repo}** — {subj}")
    lines.append("")

    # Recently modified (per repo)
    lines.append("## Recently modified source files")
    lines.append("")
    for name, info in snapshot.get("repos", {}).items():
        recent = info.get("recently_modified", [])
        if not recent:
            continue
        lines.append(f"### {name}")
        for r in recent[:5]:
            lines.append(f"- `{r.get('path')}` — {r.get('mtime')}")
        lines.append("")

    # Services
    lines.append("## Services")
    lines.append("")
    for name, info in snapshot.get("services", {}).items():
        ok = "✓" if info.get("ok") else "✗"
        lines.append(f"- {ok} **{name}** {info.get('url')} — status {info.get('status')}")
    lines.append("")

    # Build
    build = snapshot.get("builds", {}).get("last_unity_build", {})
    if build.get("available"):
        lines.append("## Last Unity build")
        lines.append("")
        size = build.get("size_mb")
        size_str = f" ({size} MB)" if size is not None else ""
        lines.append(f"- **{build.get('result', '?')}** at {build.get('at', '?')}{size_str}")
        lines.append("")

    # Memory
    mem = snapshot.get("memory", {})
    if mem.get("available"):
        lines.append("## Memory index")
        lines.append("")
        lines.append(f"- MEMORY.md mtime: {mem.get('memory_md_mtime', '?')}")
        latest = mem.get("latest_session_doc")
        if latest:
            lines.append(f"- Most recent session doc: `{latest}`")
        session_docs = mem.get("session_docs", [])
        if len(session_docs) > 1:
            lines.append("- Other recent session docs:")
            for s in session_docs[1:5]:
                lines.append(f"  - `{s.get('name')}` ({s.get('mtime')})")
        lines.append("")

    # Transcripts
    transcripts = snapshot.get("transcripts", {})
    if transcripts.get("available"):
        lines.append("## Recent Claude Code Activity")
        lines.append("")
        sf = transcripts.get("session_files", {})
        total_mb = sf.get("total_size_bytes", 0) / 1_048_576
        lines.append(f"- {sf.get('count', 0)} session transcripts ({total_mb:.1f} MB total)")
        lines.append(
            f"- {transcripts.get('total_prompts', 0)} prompts in history (C:\\Dev project)"
        )
        recent_sessions = sf.get("recent", [])
        if recent_sessions:
            lines.append(f"- Most recent session: {recent_sessions[0].get('mtime', '?')}")
        lines.append("")
        prompts = transcripts.get("recent_prompts", [])
        if prompts:
            lines.append("Last 20 prompts (newest first):")
            for p in prompts:
                ts = p.get("timestamp", "")[:16]  # YYYY-MM-DDTHH:MM
                display = p.get("display", "")
                lines.append(f"- [{ts}] {display}")
            lines.append("")

    # Claude-Mem
    cmem = snapshot.get("claude_mem", {})
    if cmem.get("available"):
        lines.append("## Claude-Mem Memory")
        lines.append("")

        summaries = cmem.get("session_summaries", [])
        if summaries:
            lines.append(f"### Recent session summaries (last {len(summaries)})")
            lines.append("")
            for s in summaries:
                lines.append(f"**Session {s.get('created_at', '?')[:16]}:**")
                if s.get("request"):
                    lines.append(f"- **Request:** {s['request']}")
                if s.get("learned"):
                    lines.append(f"- **Learned:** {s['learned']}")
                if s.get("completed"):
                    lines.append(f"- **Completed:** {s['completed']}")
                if s.get("next_steps"):
                    lines.append(f"- **Next steps:** {s['next_steps']}")
                lines.append("")

        obs = cmem.get("observations", [])
        if obs:
            lines.append(f"### Recent observations (last {len(obs)})")
            for o in obs:
                ts = o.get("created_at", "")[:10]
                lines.append(f"- [{o.get('type', '?')}] {o.get('title', '?')} ({ts})")
            lines.append("")

        cmem_prompts = cmem.get("recent_prompts", [])
        if cmem_prompts:
            lines.append(f"### Recent prompts (last {len(cmem_prompts)})")
            for p in cmem_prompts:
                ts = p.get("created_at", "")[:16]
                lines.append(f"- [{ts}] {p.get('prompt_text', '')}")
            lines.append("")

    # Tests
    tests = snapshot.get("tests", {})
    if tests:
        lines.append("## Tests (file-count proxy)")
        lines.append("")
        for name, info in tests.items():
            lines.append(f"- **{name}**: {info.get('test_file_count', '?')} test files")
        lines.append("")

    lines.append("---")
    lines.append(
        "_This document is regenerated by Director Hub's ProjectStateTracker "
        "every hour from a 15-minute scan. To force an immediate refresh: "
        "`POST http://127.0.0.1:7802/project-state/force-scan`._"
    )

    return "\n".join(lines)
