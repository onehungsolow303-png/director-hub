---
description: Mandate that all code must be original to this project — no copy-paste from external sources
paths: ["**/*"]
---

# Originality Rules — All Agents

## Core Principle
All code written for this project MUST be original — written from scratch for THIS specific app.

## Rules

1. **Always write original code** for all solutions — no copy-paste from tutorials, Stack Overflow, or external repos
2. **Always create original agents** with custom agent definitions tailored to their specific role in this project
3. **Always create original skills** with custom workflow code designed for this project's needs
4. **Rewrite external code** — When installed packages need modification, rewrite as original code for this app. Do not fork or patch external source.
5. **Use packages via import** — Standard libraries and installed packages (numpy, PIL, playwright, etc.) are used via import, not copied.
6. **Record all code changes** — Every change logged to memory/code_changes.md with what, why, and result
7. **Check memory before coding** — Read relevant memory files before writing any code
8. **Research before implementing** — Check similar approaches, read rules, then make a plan
9. **Follow rules and guidelines** — All changes follow .claude/rules/ and what-worked.md
10. **Plans before code** — Make a plan following rules and guidelines before any implementation

## What "Original" Means
- Designed specifically for this app's architecture (v5+ invert-selection, canvas-based, vanilla JS)
- Uses project-specific naming conventions and patterns
- Solves the specific problem at hand, not a generic version
- Written by the agent understanding the full project context

## What This Does NOT Prohibit
- Using standard library functions and well-known algorithms
- Importing installed packages normally
- Following established patterns already in this codebase
- Reading external projects for INSPIRATION, then writing original implementations
- Using mathematical formulas and published techniques (implemented originally)

## Enforcement
- CEO agent reviews all code changes for originality
- Master agent checks memory/code_changes.md before delegating code tasks
- Non-original code (detected copy-paste, template code) must be rewritten
