# API Automation Layer — Design Spec

**Date:** 2026-03-28
**Status:** Approved

## Overview

REST API layer for the Game UI Asset Extraction app. Exposes all app functionality programmatically via `/api/*` endpoints in serve.py. Uses Playwright headless browsers to execute the existing app.js logic — zero reimplementation of pixel processing.

## Architecture

```
External Agents / CLI
        │ JSON REST
        ▼
   serve.py :8080
   ├── Static files (GET /*)
   ├── ComfyUI proxy (/comfyui/*)
   └── API router (/api/*)
            │
    ┌───────▼────────┐
    │  Job Queue      │  In-memory dict, jobs expire after 1hr
    │  job_id→status  │
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │ Playwright Pool │  1-4 headless Chromium workers
    │ Each loads      │  pre-loaded with http://127.0.0.1:8080
    │ app.js + DOM    │  checkout/checkin for concurrency
    └───────┬────────┘
            │ page.evaluate()
            ▼
       app.js logic
       (Canvas, alpha, edge, split, enhance)
            │
            ▼
    ComfyUI :8000 (GPU segmentation)
```

## File Structure

```
api/
├── __init__.py
├── router.py           — URL routing for /api/*
├── jobs.py             — Job queue, status tracking, results store
├── pool.py             — Playwright session pool management
├── bridge.py           — Playwright ↔ app.js command bridge
└── endpoints/
    ├── __init__.py
    ├── extract.py      — POST /api/extract, POST /api/batch
    ├── config.py       — GET /api/presets, POST /api/preset, GET /api/comfyui/status
    ├── mask.py         — POST /api/mask/generate, POST /api/mask/refine
    ├── enhance.py      — POST /api/enhance
    ├── split.py        — POST /api/split
    └── workflow.py     — POST /api/workflow/build, GET /api/workflow/templates
```

## Endpoints

### Tier 1 — Core Extraction

#### POST /api/extract
Single image extraction (heuristic or AI Remove).

Request:
```json
{
  "image": "path/to/image.png",
  "preset": "dark-balanced",
  "mode": "ai-remove",
  "output_dir": "output/",
  "settings_override": {}
}
```
- `image`: local path (relative to project dir) or `data:image/png;base64,...`
- `preset`: one of the preset names from bgPresets
- `mode`: `"ai-remove"` (ComfyUI mask + extraction), `"heuristic"` (threshold-based), `"crop"` (object crop)
- `output_dir`: where to write results (default: `output/`)
- `settings_override`: optional partial settings object, overrides preset values

Response: `{ "job_id": "ext_...", "status": "queued" }`

Results (via GET /api/status):
```json
{
  "sheet": "output/image_sheet.png",
  "final": "output/image_final.png",
  "enhanced": "output/image_enhanced.png",
  "mask": "output/image_mask.png",
  "panels": [{ "index": 0, "file": "...", "width": 420, "height": 65, "score": 0.92 }],
  "alpha_stats": { "transparent": 73.8, "semi": 2.4, "opaque": 23.8 }
}
```

#### POST /api/batch
Multi-image batch extraction.

Request:
```json
{
  "images": ["a.png", "b.png", "c.png"],
  "preset": "light-balanced",
  "mode": "ai-remove",
  "ai_source": "comfyui",
  "output_dir": "output/batch_001/"
}
```
- `ai_source`: `"comfyui"`, `"browser"` (ONNX), or `"direct"` (heuristic only)

Response: `{ "job_id": "batch_...", "status": "queued", "total": 3 }`

Status includes per-image progress:
```json
{
  "status": "processing",
  "progress": 0.33,
  "current_image": "b.png",
  "completed_images": ["a.png"],
  "results": { "a.png": { "file": "output/batch_001/a_extracted.png" } }
}
```

#### GET /api/status/:jobId
Poll job progress.

Response varies by status:
- `queued`: `{ "status": "queued" }`
- `processing`: `{ "status": "processing", "progress": 0.65, "step": "..." }`
- `completed`: `{ "status": "completed", "results": {...}, "elapsed_ms": 4300 }`
- `failed`: `{ "status": "failed", "error": "...", "code": "..." }`

### Tier 2 — Configuration

#### GET /api/presets
Returns all available presets with full settings.

#### POST /api/preset
Create or update a custom preset. Custom presets stored in memory (lost on restart).

#### GET /api/comfyui/status
Returns ComfyUI connection state, GPU info, version.

### Tier 3 — Granular Pipeline Control

#### POST /api/mask/generate
Generate AI mask only without extraction. Returns mask PNG + coverage stats.

Request: `{ "image": "...", "method": "comfyui", "model": "BiRefNet-general" }`

#### POST /api/mask/refine
Apply refinement operations to an existing mask. Runs through refineImportedAiMaskAlpha.

Request: `{ "mask": "...", "image": "...", "expand": 2, "feather": 1, "invert": false, "threshold": 128 }`

#### POST /api/enhance
Run AI Enhance (color restoration) on an already-extracted result.

Request: `{ "extracted": "...", "original": "..." }`

#### POST /api/split
Run split panel detection on an extracted image.

Request: `{ "image": "...", "min_pixels": 5000, "alpha_cutoff": 220 }`

### Tier 4 — Workflow Builder

#### POST /api/workflow/build
Generate ComfyUI workflow JSON from configuration parameters.

Request:
```json
{
  "workflow_type": "combined",
  "art_style": "fantasy",
  "checkpoint": "juggernautXL",
  "remover": "essentials",
  "asset_type": "UI panel",
  "material": "ornate gold border"
}
```

#### GET /api/workflow/templates
List available starter workflow templates with file paths.

## Key Components

### Playwright Session Pool (pool.py)

- Manages 1-4 headless Chromium browser contexts
- Each context has one page pre-navigated to http://127.0.0.1:8080
- `checkout()` returns an available page, blocks if all busy
- `checkin(page)` returns page to pool after job completes
- `reset(page)` clears app state between jobs (reload if needed)
- Pool created on server startup, torn down on shutdown
- Uses asyncio for non-blocking pool management in threaded server

### Bridge (bridge.py)

Translates API parameters into page.evaluate() calls:
- `load_image(page, path)` — triggers file chooser, loads image
- `apply_preset(page, name)` — selects preset in dropdown
- `apply_settings(page, overrides)` — sets individual form controls
- `run_ai_remove(page)` — clicks AI Remove, polls for completion
- `run_process(page)` — clicks Process Image, polls for completion
- `extract_results(page, output_dir)` — reads canvas data, saves PNGs
- `extract_alpha_stats(page)` — reads alpha channel statistics
- `extract_panels(page, output_dir)` — saves split panel PNGs
- `run_enhance(page)` — clicks AI Enhance, extracts result
- `get_comfyui_status(page)` — reads connection status from DOM
- `generate_mask_only(page)` — runs mask generation without extraction
- `build_workflow(page, config)` — fills workflow builder form, extracts JSON

### Job Manager (jobs.py)

- In-memory dict: `jobs = { job_id: { status, progress, step, results, error, created_at } }`
- Job IDs: `{type}_{timestamp}_{counter}` (e.g., `ext_1711612800_001`)
- Jobs expire after 1 hour (cleanup on access)
- Thread-safe with Lock
- Status transitions: queued → processing → completed/failed

### Router (router.py)

- Parses `/api/{endpoint}` paths
- Dispatches to endpoint handlers
- Handles JSON parsing, error formatting, CORS
- Validates required fields before dispatching

## Conventions

- All image paths relative to project directory unless absolute
- Base64 input accepted: `"data:image/png;base64,..."`
- Async jobs for anything >1s, sync for instant operations
- Error format: `{ "error": "message", "code": "ERROR_CODE" }`
- Error codes: `NO_IMAGE`, `INVALID_PRESET`, `COMFYUI_DISCONNECTED`, `POOL_EXHAUSTED`, `JOB_NOT_FOUND`
- Output files written to `output/` by default, auto-created
- Content-Type: application/json for all API responses

## What Stays Untouched

- app.js — zero changes
- index.html — zero changes
- styles.css — zero changes
- serve.py — minimal additions (import router, add API dispatch in handler)
- The browser UI continues working exactly as before

## Dependencies

- playwright (already installed in .venv)
- No new dependencies required
