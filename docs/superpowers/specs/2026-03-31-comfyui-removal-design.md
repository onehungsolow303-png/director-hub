# Design Spec: Surgical ComfyUI Removal (Approach A)

**Date:** 2026-03-31
**Goal:** Remove all ComfyUI dependencies from the app, making it fully self-contained with browser ONNX as the primary AI mask source. No APIs, no subscriptions, no local installs beyond the app itself.

**Motivation:** ComfyUI requires local installation, launches a separate desktop app, adds proxy complexity, and uses local GPU that can't compete with cloud hardware. The app's core extraction pipeline (v5+ detection, multi-spectrum cleanup, manual tools) already works without ComfyUI. Browser ONNX segmentation already provides AI mask generation without external dependencies. Removing ComfyUI eliminates the biggest dependency and moves toward a deployable web app.

## What Gets Removed

### app.js (~300 lines removed)

**Top-level config objects (lines 1-30):**
- `stylePresets` — fantasy/scifi/pixel/clean prompt templates (ComfyUI generation)
- `checkpoints` — Juggernaut XL/Flux/SDXL model configs (ComfyUI generation)
- `removers` — ComfyUI node pack configs (essentials/bria/was/ben2)

**ComfyUI DOM references (lines 189-198):**
- `comfyuiServer`, `comfyuiModel`, `comfyuiConnectButton`, `comfyuiGenerateMaskButton`
- `comfyuiStatus`, `comfyuiDot`

**ComfyUI state variable (line 235):**
- `comfyuiConnected`

**ComfyUI `comfyui` property in `bgPresets` (lines 42-84):**
- Remove the `comfyui: { model, mask_blur, ... }` property from each preset object

**ComfyUI API integration section (~lines 1047-1260):**
- `getComfyuiBaseUrl()`
- `testComfyuiConnection()`
- `comfyuiUploadImage()`
- `getActiveComfyuiConfig()`
- `buildSegmentationWorkflow()`
- `comfyuiQueueWorkflow()`
- `comfyuiPollForCompletion()`
- `extractOutputImageFilename()`
- `comfyuiDownloadImage()`
- `generateComfyuiMask()`
- `generateComfyuiMaskForImage()`

**Tab 2 workflow builder functions (~lines 186-290):**
- `formStateToConfig()`
- `buildPrompts()`
- `buildInstallList()`
- `buildSteps()`
- `buildWorkflowTemplate()`
- `renderChecklist()`
- `renderSteps()`
- `refreshOutput()`

**Tab 2 DOM references (lines ~161-172):**
- `form`, `installList`, `stepsList`, `positivePrompt`, `negativePrompt`
- `workflowJson`, `copyJsonButton`, `downloadJsonButton`, `loadDemoButton`, `copyChecklistButton`

**Scattered references to update:**
- `updateActionStates()` — remove `comfyuiConnected` checks
- `updateMaskStatusBlock()` — remove ComfyUI status text
- `getIdleGuidanceMessage()` — remove ComfyUI connection references
- `applyPreset()` — remove `comfyui` property handling
- Event listeners for `comfyuiConnectButton`, `comfyuiGenerateMaskButton`
- Batch mode `comfyui` option handling in `processBatchImages()`
- `showTab()` function and tab initialization code

### index.html

**Tab 2 removal (lines 333-454):**
- Remove entire `<div class="tab-page" id="tab-workflow">` section
- Remove tab navigation buttons/links

**ComfyUI controls in Tab 1 (lines 55, 67-80, 123-133):**
- Remove `comfyui` option from batch `<select id="batchAiSource">`
- Remove Segmentation Model `<select id="comfyuiModel">` and label
- Remove ComfyUI status dot and text `<span id="comfyuiDot">`, `<span id="comfyuiStatus">`
- Remove "ComfyUI & AI Mask" tool group label
- Remove ComfyUI Server `<input id="comfyuiServer">` and label
- Remove "Test Connection" `<button id="comfyuiConnectButton">`
- Rename "Quick Mask (Browser)" button to "Generate AI Mask" (now primary)
- Remove "Generate AI Mask" `<button id="comfyuiGenerateMaskButton">` (was ComfyUI-powered)

### serve.py

**ComfyUI auto-launch (~lines 20-77):**
- Remove `COMFYUI_EXE` path constant
- Remove `COMFYUI_PORTS` list
- Remove `COMFYUI_BASE` global
- Remove `find_comfyui_port()`
- Remove `ensure_comfyui_running()`
- Remove call to `ensure_comfyui_running()` in startup

**ComfyUI proxy handler (~lines 102-160):**
- Remove `/comfyui/*` proxy in `do_GET` and `do_POST`
- Remove `/save-mask` endpoint and `handle_save_mask()` method

### api/endpoints/workflow.py

- Delete entire file (ComfyUI workflow builder endpoint)
- Remove registration in `api/router.py`

### Other files to delete

- `starter-workflow-background-removal-only.json`
- `starter-workflow-juggernaut-fantasy.json`
- `starter-workflow-pixel-ui-background-removal.json`
- `custom_nodes/` directory (ComfyUI node packs)

## What Stays Untouched

- `buildBlackBorderUiMask()` — core v5+ detection engine (pure JS)
- `buildStructuralUiMask()` — fallback detection (pure JS)
- `generateBrowserMask()` / `generateBrowserMaskForImage()` — browser ONNX segmentation (becomes primary AI path)
- `loadOnnxModel()` — ONNX Runtime Web model loading
- `aiRemoveWorkflow()` — two-pass architecture (JS v5+ detection + Python multi-spectrum cleanup). Already ComfyUI-free.
- `processBackgroundRemoval()` — main extraction pipeline
- `processBatchImages()` — batch processing (minus ComfyUI option)
- All manual tools (brush, boxes, sampling, presets, corrections)
- `border_detect/` Python package — multi-spectrum pipeline
- API endpoints: extract, mask, enhance, split, border-detect, config
- `scripted/` batch removal tools
- All test infrastructure (pytest, Playwright, quality gates)
- All CSS — no visual changes needed
- `u2netp.onnx` — the browser ONNX model file

## UI After Removal

### AI Remove card (unchanged behavior)
- Source image input
- Batch mode toggle
- Background tone selector
- **"AI Remove" button** — runs v5+ detection + multi-spectrum cleanup (no change)
- Status text

### AI Mask tools (simplified)
- **"Generate AI Mask" button** — runs browser ONNX segmentation (was "Quick Mask (Browser)")
- "Load AI Mask PNG" button — import external mask file
- Browser AI status text
- Mask refinement controls (unchanged)

### Removed from UI
- ComfyUI server URL field
- Test Connection button
- Old "Generate AI Mask" button (ComfyUI-powered)
- Segmentation Model dropdown
- ComfyUI connection status dot
- Tab 2 (Workflow Builder) and tab navigation

## Risk Assessment

- **Low risk:** All removed code is ComfyUI-specific. No extraction logic changes.
- **AI Remove path is already ComfyUI-free.** The two-pass architecture (v5+ JS → Python multi-spectrum) doesn't touch ComfyUI.
- **Browser ONNX already works.** Just relabeling and promoting it.
- **Test suite should still pass** — tests use AI Remove and Process Image, which don't depend on ComfyUI.

## Future (Approach B → C)

After A is validated:
- **B:** Consolidate AI mask UI (2 clean paths: ONNX + import)
- **C:** Restructure serve.py for web deployment, bundle ONNX model, remove Playwright pool from production path
