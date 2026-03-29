# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Stack

JavaScript (vanilla, no bundler), HTML/CSS, Python. Always verify the current state of UI code before editing — no blind modifications.

## Development Commands

**Run the dev server:**
```bash
python serve.py
# Serves at http://127.0.0.1:8080
```

**Visual testing (Playwright screenshots):**
```bash
python screenshot.py [url] [output_path] [click_selector]
```

**Batch background removal:**
```powershell
$env:PYTHONPATH="C:\Dev\Image generator\.venv\Lib\site-packages"
& python "C:\Dev\Image generator\scripted\remove_black_bg.py" --input-dir <dir> --output-dir <dir> --preset ui-soft
# Presets: ui-balanced, ui-soft, ui-hard
```

The app also opens directly in the browser via `index.html` — the Python server is only needed for ComfyUI CORS proxying and the `/save-mask` endpoint.

## Architecture

The app is a browser-based game UI asset extraction tool. Core files:

- **`index.html`** — Two-tab layout: Extraction tab and Workflow Builder tab
- **`app.js`** — All application logic (~4000 lines, vanilla JS, no bundler)
- **`styles.css`** — Dark theme, CSS Grid layout
- **`serve.py`** — Dev HTTP server + CORS proxy to ComfyUI + `/save-mask` endpoint

### Extraction Pipeline (app.js)

Extraction runs entirely in the browser using HTML5 Canvas pixel manipulation — no external image libraries. The pipeline has four modes selected by the user: `remove`, `crop`, `multi`, `ai`.

**Layered mask system** — three independent alpha sources that can be combined:
1. `importedAiMaskAlpha` — external high-quality mask imported from ComfyUI or file
2. `processedMaskCanvas/Alpha` — heuristic-generated mask from the active extraction mode
3. `manualMaskCanvas` — brush corrections painted by the user

Key pipeline functions:
- `processBackgroundRemoval()` — main entry point for extraction
- `buildAlphaData()` — flood-fill based alpha generation from background samples
- `refineAlphaData()` — secondary polish pass
- `applyManualCorrectionsToAlpha()` — merges keep/subtract points, boxes, and brush strokes
- `findMaskComponentBoxes()` — detects separated components for the split gallery
- `buildProcessedBackgroundFromAlpha()` — final compositing

**Manual correction tools** accumulate and never overwrite each other: background sample points (up to 6), keep points (up to 12), keep boxes (up to 24), subtract boxes, and brush strokes with undo.

**Split gallery** auto-detects separated panels from the mask, sorts by size/usefulness, and lets the user promote any panel to the main result.

### ComfyUI Integration

`serve.py` proxies requests to the ComfyUI server to avoid CORS. The browser:
1. Builds a workflow JSON from the Workflow Builder tab (or starter templates)
2. POSTs to ComfyUI via the proxy
3. Polls for completion
4. Downloads generated masks via `/save-mask`

Starter workflow templates: `starter-workflow-*.json` (three presets for background removal, Juggernaut XL, and pixel UI).

Supported segmentation model packs: BiRefNet, RMBG, InSPyReNet, BEN2 (configured via `removers` map in app.js).

### Browser AI (ONNX Runtime)

When ComfyUI is unavailable, the app can load a local U2-Net ONNX model and run inference in-browser as a fallback.

## Architecture Planning

For multi-step AI pipelines (detect → segment → extract), **always propose the full architecture and get user confirmation BEFORE implementing**. Never assume a single-pass approach when the user describes multiple stages. Outline each step with expected inputs/outputs and potential pitfalls.

When debugging, use the `/debug` skill for structured diagnosis.

## Image Processing Guidelines

- Always test canvas/image operations with a minimal example first before building the full pipeline.
- Watch for canvas tainting from cross-origin images — use the proxy or OffscreenCanvas.
- Alpha channel handling: explicitly verify mask polarity (0=transparent vs 0=opaque) at each stage.
- When working with masks, log dimensions, value ranges, and channel count before processing.

## Key Constraints

- **Full-sheet layout is the primary output** — do not optimize for cropped assets at the expense of the full sheet result.
- **Manual correction tools must remain accessible** — never hide them behind AI-only flows.
- **Preserve UI asset quality above all** — background removal must not destroy ornate UI details.
- After any code change, check for secondary regressions before finishing. (Syntax errors are caught automatically by PostToolUse hooks.)
- Use `screenshot.py` / Playwright to verify visual UI changes — do not edit CSS/HTML without visual confirmation.

## Configured Features (.claude/settings.json)

### Hooks
- **Model file protection** — PreToolUse hook blocks edits to `.onnx`, `.safetensors`, `.pth`, `.bin`, `.pt` files.
- **Post-edit checks** — Single PostToolUse hook: screenshot reminder for HTML/CSS, `node --check` for JS, `py_compile` for Python.

### Environment Variables
- `COMFYUI_URL` = `http://127.0.0.1:8000` (ComfyUI backend)
- `APP_URL` = `http://127.0.0.1:8080` (dev server)

### Permissions
Pre-approved: file reads/writes/edits, glob/grep, serve.py, screenshot.py, curl to localhost, git commands.
Blocked: `rm -rf`, `git push --force`, `git reset --hard`.

## Useful Skills

- **`/debug`** — Structured debugging: reproduce → isolate → identify root cause → minimal fix → verify → check adjacents. Use this instead of speculative fixing.
- **`/simplify`** — Run after refactoring to catch redundancy in app.js canvas code.
- **`/loop 2m <prompt>`** — Poll ComfyUI status or monitor extraction jobs while working.
