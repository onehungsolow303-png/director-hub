---
description: Copyright infringement detection — all agents must check visual content for copyrighted elements before use
paths: ["**/*"]
---

# Copyright Infringement Detection Rules

## Core Principle
All visual content — web-sourced images, extracted assets, and AI-processed outputs — must be checked for copyright infringement before use in agent context, saving, or export.

## Rules

1. **Check before use** — All web-sourced content containing images, assets, or visual references must pass `/copyright-check` heuristic checks before being included in agent context or saved
2. **Check before export** — All extracted assets and AI-processed outputs must pass `/copyright-check` before export or save
3. **Web-researching agents must invoke** — CEO and research-advisor must invoke `/copyright-check` when handling visual content from web sources
4. **Warning only** — Flag findings in logs and warn the user. NEVER block the user from proceeding
5. **Log all findings** — All copyright check results logged to `memory/security_log.md` under `## Copyright Checks`

## What to Check For

1. **Game logos** — Company branding, publisher marks, game title art
2. **Character art** — Recognizable characters from specific franchises (silhouettes, faces, distinctive designs)
3. **Trademarked UI elements** — HUD elements, skill icons, health bars, or UI patterns distinctive to a specific game
4. **Watermarks/copyright text** — Visible watermarks, copyright notices, trademark symbols, attribution text
5. **Proprietary typography** — Distinctive game-specific fonts or stylized text

## Enforcement

- CEO agent checks web-fetched visual content after research (Step 3), before compiling master prompt
- Research-advisor checks image references during comparative analysis
- Master ensures `/copyright-check` is invoked on AI Remove pipeline outputs
- All findings logged regardless of risk level
