---
name: copyright-check
description: Heuristic copyright infringement check for visual content — web-sourced images, extracted assets, and AI-processed outputs. Warning-only, logs all findings.
---

# Copyright Infringement Check

Use this skill when handling visual content from web sources, reviewing extracted assets, or evaluating AI-processed outputs.

## When to Use

- After web research that includes visual content (images, screenshots, asset references)
- Before including visual references in agent prompts
- When reviewing extracted UI assets for export
- When evaluating AI Remove pipeline outputs

## Heuristic Checklist

Walk through each check IN ORDER. For each, assess as `clear`, `uncertain`, or `flagged`.

### 1. Game Logos
Examine the content for recognizable company branding, publisher marks, or game title art.
- Look for: stylized text logos, publisher emblems, franchise wordmarks
- Common locations: corners of screenshots, splash screens, loading bars, title bars
- Assess: `clear` | `uncertain` | `flagged`

### 2. Character Art
Examine for recognizable characters from specific game franchises.
- Look for: character portraits, silhouettes, faces, distinctive character designs
- Consider: iconic poses, franchise-specific art styles, named characters
- Assess: `clear` | `uncertain` | `flagged`

### 3. Trademarked UI Elements
Examine for HUD elements or UI patterns distinctive to a specific game.
- Look for: proprietary health/mana bar designs, unique skill icon sets, game-specific minimap styles
- Consider: whether the UI pattern is generic (common across many games) or distinctive (identifiable to one game)
- Generic UI patterns (rectangular health bars, grid inventories) are `clear`
- Assess: `clear` | `uncertain` | `flagged`

### 4. Watermarks / Copyright Text
Examine for visible watermarks, copyright notices, or trademark symbols.
- Look for: (c) notices, (TM)/(R) symbols, "All Rights Reserved" text, semi-transparent watermark overlays
- Check: image corners, bottom edges, overlay text
- Assess: `clear` | `uncertain` | `flagged`

### 5. Proprietary Typography
Examine for distinctive game-specific fonts or stylized text.
- Look for: custom fantasy/sci-fi fonts, stylized UI text that matches a known game's aesthetic
- Consider: whether the font is a common system/web font or a custom game-specific typeface
- Assess: `clear` | `uncertain` | `flagged`

## Risk Assessment

After completing all 5 checks, determine overall risk:

- **Low**: All checks are `clear`
- **Medium**: One check is `uncertain`, no checks are `flagged`
- **High**: Any check is `flagged` OR two or more checks are `uncertain`

## Warning Trigger

Show a warning to the user when:
- Any heuristic is `flagged`, OR
- Two or more heuristics are `uncertain`

The warning MUST describe:
- What was detected (which heuristic, what specifically)
- The source (URL or asset path)
- The warning does NOT block the user from proceeding

## Logging

Log ALL results (including clean passes) to `memory/security_log.md` under `## Copyright Checks` using this format:

```
### Copyright Check — {YYYY-MM-DD}
- **Source**: {URL or asset path}
- **Game logos**: {clear|uncertain|flagged} — {brief details}
- **Character art**: {clear|uncertain|flagged} — {brief details}
- **Trademarked UI**: {clear|uncertain|flagged} — {brief details}
- **Watermarks/text**: {clear|uncertain|flagged} — {brief details}
- **Typography**: {clear|uncertain|flagged} — {brief details}
- **Overall risk**: {low|medium|high}
- **Action**: {warning shown to user / no action needed}
```

## Rules
- NEVER block the user — warnings only
- ALWAYS log findings regardless of risk level
- ALWAYS show warning to user when risk is high
- Be specific in details — name the game/franchise if you can identify it
- When uncertain, err on the side of flagging — false positives are preferable to missed copyright issues
