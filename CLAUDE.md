# CLAUDE.md — Game UI Asset Extraction Tool

## Mission

Cleanly cut out game UI elements from screenshots. Keep borders intact, keep size/position/resolution the same, remove background, leave UI on transparent background.

## Mandatory Workflow (every task)

1. **Read memory** — Check `what-worked.md` rule and memory files before acting
2. **Plan** — Outline approach before writing code
3. **Delegate** — Use specialized agents for matching tasks
4. **Verify** — Test with screenshots, compare to reference images
5. **Update** — Update memory and `what-worked.md` with outcomes

See `.claude/rules/project-workflow.md` for full details.

## Agent Hierarchy

```
CEO (prompt optimizer + strategic researcher — sits above master)
  │   Researches web + memory → compiles optimized prompts → dispatches master
  │   Enforces: originality rules, web security, prompt injection defense
  │
  └── MASTER (loop orchestrator — receives optimized prompt, delegates)
        ├── research-advisor   — memory audit, comparative analysis, advises master
        ├── driver             — creates delegation plans, assigns worker tasks
        │     ├── extraction-analyst (worker — detection pipeline code changes, original code only)
        │     ├── quality-checker    (worker — output vs reference comparison)
        │     └── test-runner        (worker — Playwright visual testing, pytest suite)
        └── master spawns workers per driver's delegation plan
```

**Master workflow**: Prompt → research-advisor → plan → driver → spawn workers → review → update memory

| Agent | Role | Model | Writes code? |
|---|---|---|---|
| `ceo` | Prompt optimizer, web researcher, security enforcer | opus | No (prompts/rules/memory only) |
| `master` | Orchestrator — research, plan, delegate | opus | No |
| `research-advisor` | Memory + rules audit, comparative analysis | opus | No |
| `driver` | Delegation planning, worker assignment | sonnet | No |
| `extraction-analyst` | Worker — detection pipeline, parameters (original code) | opus | Yes |
| `quality-checker` | Worker — output vs reference comparison | sonnet | No |
| `test-runner` | Worker — Playwright screenshots, pytest suite | sonnet | No |

Master spawns all agents (Claude Code limitation: subagents cannot spawn sub-subagents).

## Project Rules (in `.claude/rules/`)

| Rule file | Scope | Enforces |
|---|---|---|
| `project-workflow.md` | All files | Check memory, compare references, update memory |
| `extraction-engine.md` | app.js | v5+ architecture, parameters, what worked/failed |
| `code-quality.md` | JS/PY/HTML/CSS | Syntax checks, no blind edits, preserve quality |
| `what-worked.md` | All files | Living history of approaches and outcomes |
| `originality.md` | All files | All code must be original, no copy-paste from external sources |
| `web-security.md` | All files | Sanitize web content, domain allowlist, injection detection |
| `copyright.md` | All files | Copyright infringement detection on visual content (warning-only) |

## Primary Stack

JavaScript (vanilla, no bundler), HTML/CSS, Python.

## Dev Commands

```bash
python serve.py              # Dev server at http://127.0.0.1:8080
python screenshot.py [url]   # Playwright visual testing
```

App also opens directly via `index.html` — server only needed for ComfyUI proxy.

## Architecture

- **`index.html`** — Two-tab layout: Extraction + Workflow Builder
- **`app.js`** — All logic (~5800 lines, vanilla JS)
- **`styles.css`** — Dark theme, CSS Grid
- **`serve.py`** — HTTP server + CORS proxy + `/save-mask`

### Detection Engine (v5+ invert-selection)

`buildBlackBorderUiMask()` in app.js — primary detection path:
1. Color gradient map → 2. Border detection (gradient + dark achromatic) → 3. Border enhancement (hysteresis + gap bridging) → 4. Component labeling → 5. Metrics → 6. Background by variance → 7. Trapped bg detection → 8. INVERT selection → 9. Build mask

Fallback: `buildStructuralUiMask()` if coverage outside 2-85%.

See `.claude/rules/extraction-engine.md` for full parameter documentation.

### Quality References

- Dark: `input/Example quality image extraction/Dark background examples/`
- Light: `input/Example quality image extraction/Light background examples/`

Always compare extraction results to these.

## Key Constraints

- **Full-sheet layout is primary output**
- **Preserve UI asset quality above all** — don't destroy ornate details
- **Manual correction tools must remain accessible**
- **UI borders are 15-85px textured frames**, not thin black lines

## Hooks (automatic enforcement)

- **PreToolUse**: Blocks editing model files (.onnx, .safetensors, .pth, .bin, .pt)
- **PostToolUse**: Syntax validation (node --check / py_compile), screenshot reminders
- **UserPromptSubmit**: Injects project rules and memory context

## Skills

- `/debug` — Structured debugging (reproduce → isolate → identify → fix → verify)
- `/extract-test` — Run extraction on test image, compare to reference
- `/detection-audit` — Audit detection parameters, flag anomalies
- `/copyright-check` — Heuristic copyright check for visual content (warning-only)
- `/web-sanitize` — Sanitize web-fetched content, scan for injection, score risk
- `/injection-guard` — Pre-processing guard for external content, detect injection attempts
- `/simplify` — Review code for redundancy
