# ComfyUI Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all ComfyUI dependencies from Gut It Out, making it a self-contained extraction app with browser ONNX as the primary AI mask source.

**Architecture:** Surgical removal — delete ComfyUI-specific code from app.js, index.html, and serve.py. Rewire the one ComfyUI fallback in AI Remove to use browser ONNX instead. Remove Tab 2 (Workflow Builder) entirely. No new features, no logic changes to the extraction pipeline.

**Tech Stack:** Vanilla JS, HTML, CSS, Python (serve.py)

**Spec:** `docs/superpowers/specs/2026-03-31-comfyui-removal-design.md`

---

## File Structure

No new files. Modifications only:

| File | Action | Responsibility |
|------|--------|----------------|
| `app.js` | Modify | Remove ~400 lines of ComfyUI code, rewire 3 functions |
| `index.html` | Modify | Remove Tab 2, ComfyUI controls, simplify sidebar |
| `serve.py` | Modify | Remove ComfyUI launch/proxy, workflow endpoint |
| `api/endpoints/workflow.py` | Delete | ComfyUI workflow builder endpoint |
| `starter-workflow-*.json` | Delete | ComfyUI workflow templates (3 files) |

---

### Task 1: Remove Tab 2 (Workflow Builder) from index.html

**Files:**
- Modify: `index.html:12-17` (sidebar nav)
- Modify: `index.html:333-454` (Tab 2 content)
- Modify: `index.html:458-467` (tab switcher script)

- [ ] **Step 1: Remove the Workflow Builder sidebar link**

In `index.html`, replace the sidebar nav section (lines 12-17):

```html
    <nav class="sidebar">
      <div class="sidebar-brand">Gut It Out</div>
      <div class="sidebar-group">Tools</div>
      <a class="sidebar-link active" data-tab="extraction">Extraction</a>
      <a class="sidebar-link" data-tab="workflow">Workflow Builder</a>
    </nav>
```

With:

```html
    <nav class="sidebar">
      <div class="sidebar-brand">Gut It Out</div>
    </nav>
```

- [ ] **Step 2: Remove Tab 2 HTML content**

Delete the entire Workflow Builder tab section (lines 333-454), from `<!-- ══ TAB: Workflow Builder ══ -->` through `</div><!-- end tab-workflow -->`.

- [ ] **Step 3: Remove tab switcher script**

Replace the inline script block (lines 458-467):

```html
  <script>
  function showTab(name){
    document.querySelectorAll('.tab-page').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.sidebar-link').forEach(l=>l.classList.remove('active'));
    var tab=document.getElementById('tab-'+name);if(tab)tab.classList.add('active');
    var link=document.querySelector('.sidebar-link[data-tab="'+name+'"]');if(link)link.classList.add('active');
  }
  document.querySelectorAll('.sidebar-link[data-tab]').forEach(function(l){
    l.addEventListener('click',function(){showTab(this.dataset.tab);});
  });
  </script>
```

With nothing (delete the entire `<script>` block). The extraction tab has `class="tab-page active"` already set, so it will display by default. The `.tab-page` CSS rule (`display:none`) only hides non-active tabs.

- [ ] **Step 4: Remove the `id="tab-extraction"` wrapper div**

Since there's only one tab now, simplify: remove the opening `<div class="tab-page active" id="tab-extraction">` (line 27) and its closing `</div><!-- end tab-extraction -->` (line 331). The content inside stays — just unwrap it from the tab div.

- [ ] **Step 5: Verify HTML renders correctly**

Run: `node -e "const fs=require('fs'); const h=fs.readFileSync('index.html','utf8'); console.log('OK: '+h.length+' chars'); if(h.includes('tab-workflow'))throw new Error('tab-workflow still present');"` from the `Image generator` directory.

Expected: `OK: XXXX chars` with no error.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "refactor: remove Workflow Builder tab and tab navigation from HTML"
```

---

### Task 2: Remove ComfyUI controls from index.html

**Files:**
- Modify: `index.html:55` (batch comfyui option)
- Modify: `index.html:66-80` (segmentation model + status)
- Modify: `index.html:123-133` (ComfyUI server + buttons)

- [ ] **Step 1: Remove comfyui option from batch dropdown**

In `index.html`, find the `<select id="batchAiSource">` and remove the comfyui option line:

```html
                <option value="comfyui">AI mask via ComfyUI + background removal (2-pass)</option>
```

The remaining options (`direct` and `browser`) stay.

- [ ] **Step 2: Remove Segmentation Model dropdown and ComfyUI status**

Delete lines 66-80 (from `<label class="field">` with "Segmentation Model" through the closing `</div>` of the comfyui status row):

```html
            <label class="field">
              <span>Segmentation Model</span>
              <select id="comfyuiModel">
                <option value="BiRefNet-general">BiRefNet General</option>
                <option value="BiRefNet-HR">BiRefNet HR</option>
                <option value="BiRefNet_512x512">BiRefNet 512 (fast)</option>
                <option value="RMBG-2.0">RMBG 2.0</option>
                <option value="INSPYRENET">InSPyReNet</option>
                <option value="BEN2">BEN2</option>
              </select>
            </label>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
              <span id="comfyuiDot" style="width:8px;height:8px;border-radius:50%;background:#666;display:inline-block"></span>
              <span id="comfyuiStatus" class="helper-copy" style="margin:0;font-size:12px">ComfyUI: checking...</span>
            </div>
```

- [ ] **Step 3: Replace ComfyUI & AI Mask tool group**

Replace lines 123-133 (the "ComfyUI & AI Mask" tool group):

```html
            <div class="tool-group-label">ComfyUI &amp; AI Mask</div>
            <label class="field">
              <span>ComfyUI Server</span>
              <input id="comfyuiServer" type="text" value="http://127.0.0.1:8000" placeholder="http://127.0.0.1:8000">
            </label>
            <div class="btn-row" style="margin-bottom:10px">
              <button id="comfyuiConnectButton" class="ghost-button" type="button">Test Connection</button>
              <button id="comfyuiGenerateMaskButton" class="primary-button" type="button">Generate AI Mask</button>
              <button id="browserMaskButton" class="ghost-button" type="button">Quick Mask (Browser)</button>
            </div>
            <p id="browserMaskStatus" class="helper-copy">Browser AI: model not loaded</p>
```

With:

```html
            <div class="tool-group-label">AI Mask</div>
            <div class="btn-row" style="margin-bottom:10px">
              <button id="browserMaskButton" class="primary-button" type="button">Generate AI Mask</button>
            </div>
            <p id="browserMaskStatus" class="helper-copy">Browser AI: model not loaded</p>
```

- [ ] **Step 4: Verify HTML is valid**

Run: `node -e "const fs=require('fs'); const h=fs.readFileSync('index.html','utf8'); console.log('OK: '+h.length+' chars'); if(h.includes('comfyuiServer'))throw new Error('comfyuiServer still present'); if(h.includes('comfyuiModel'))throw new Error('comfyuiModel still present');"` from the `Image generator` directory.

Expected: `OK: XXXX chars` with no error.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "refactor: remove ComfyUI controls from extraction tab HTML"
```

---

### Task 3: Remove ComfyUI code from app.js — Top section

**Files:**
- Modify: `app.js:1-31` (stylePresets, checkpoints, removers)
- Modify: `app.js:42,50,58,68,76,84` (comfyui property in bgPresets)
- Modify: `app.js:88-97` (Tab 2 DOM refs)
- Modify: `app.js:189-193,198` (ComfyUI DOM refs)
- Modify: `app.js:224` (currentPayload variable)
- Modify: `app.js:235` (comfyuiConnected variable)

- [ ] **Step 1: Delete stylePresets, checkpoints, and removers objects**

Delete lines 1-31 of `app.js` (the three config objects: `stylePresets`, `checkpoints`, `removers`). These are only used by Tab 2 workflow builder functions.

- [ ] **Step 2: Remove comfyui property from each bgPreset**

In each of the 6 preset objects in `bgPresets`, delete the `comfyui: { ... }` line. For example, in `"dark-balanced"`, delete:

```js
    comfyui: { model: "RMBG-2.0", mask_blur: 0, mask_offset: 0, sensitivity: 1.0, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
```

Do this for all 6 presets: `dark-balanced`, `dark-soft`, `dark-hard`, `light-balanced`, `light-soft`, `light-hard`.

- [ ] **Step 3: Delete Tab 2 DOM references**

Delete these lines (originally lines 88-97):

```js
const form = document.querySelector("#workflowForm");
const installList = document.querySelector("#installList");
const stepsList = document.querySelector("#stepsList");
const positivePrompt = document.querySelector("#positivePrompt");
const negativePrompt = document.querySelector("#negativePrompt");
const workflowJson = document.querySelector("#workflowJson");
const copyJsonButton = document.querySelector("#copyJsonButton");
const downloadJsonButton = document.querySelector("#downloadJsonButton");
const loadDemoButton = document.querySelector("#loadDemoButton");
const copyChecklistButton = document.querySelector("#copyChecklistButton");
```

- [ ] **Step 4: Delete ComfyUI DOM references and state variable**

Delete these lines:

```js
const comfyuiServer = document.querySelector("#comfyuiServer");
const comfyuiModel = document.querySelector("#comfyuiModel");
const comfyuiConnectButton = document.querySelector("#comfyuiConnectButton");
const comfyuiGenerateMaskButton = document.querySelector("#comfyuiGenerateMaskButton");
const comfyuiStatus = document.querySelector("#comfyuiStatus");
```

And:

```js
const comfyuiDot = document.querySelector("#comfyuiDot");
```

And:

```js
let comfyuiConnected = false;
```

And:

```js
let currentPayload = null;
```

- [ ] **Step 5: Run syntax check**

Run: `node --check app.js` from the `Image generator` directory.

Expected: No output (clean syntax).

- [ ] **Step 6: Commit**

```bash
git add app.js
git commit -m "refactor: remove ComfyUI config objects, DOM refs, and state from app.js top section"
```

---

### Task 4: Remove ComfyUI functions from app.js — Middle section

**Files:**
- Modify: `app.js` — delete Tab 2 functions (~lines 272-371 after Task 3 shifts)
- Modify: `app.js` — delete ComfyUI API section (~lines 1047-1300 after Task 3 shifts)

Note: Line numbers will shift after Task 3. Use function names to locate code, not line numbers.

- [ ] **Step 1: Delete Tab 2 functions**

Delete these 8 functions and the `refreshOutput` call at the bottom:

```js
function formStateToConfig() { ... }
function buildPrompts(config) { ... }
function buildInstallList(config) { ... }
function buildSteps(config) { ... }
function buildWorkflowTemplate(config, prompts) { ... }
function renderChecklist(items) { ... }
function renderSteps(steps) { ... }
function refreshOutput(config) { ... }
```

Search for `function formStateToConfig` and delete through the end of `refreshOutput`.

- [ ] **Step 2: Delete the entire ComfyUI API Integration section**

Search for `// --- ComfyUI API Integration ---` and delete everything from that comment through the end of `generateComfyuiMask()` (the function that ends with the closing brace after `if (bgStatus) bgStatus.textContent = \`ComfyUI mask generation failed`).

Functions to delete:
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

- [ ] **Step 3: Delete generateComfyuiMaskForImage()**

Search for `async function generateComfyuiMaskForImage` and delete the entire function (near line 2850 originally).

- [ ] **Step 4: Run syntax check**

Run: `node --check app.js` from the `Image generator` directory.

Expected: No output (clean syntax). If there are errors, they will be from references to deleted functions — those are fixed in Task 5.

- [ ] **Step 5: Commit (if syntax passes)**

```bash
git add app.js
git commit -m "refactor: remove ComfyUI API integration and workflow builder functions from app.js"
```

---

### Task 5: Rewire ComfyUI references in app.js — Scattered references

**Files:**
- Modify: `app.js` — update `updateMaskStatusBlock()`, `getIdleGuidanceMessage()`, `applyPreset()`, `aiRemoveWorkflow()` ComfyUI fallback, `processBatchImages()`, event listeners, initialization

- [ ] **Step 1: Fix updateMaskStatusBlock()**

Find the `updateMaskStatusBlock` function. Replace the `aiLabel` block:

```js
  const aiLabel = comfyuiConnected
    ? "AI hook: ComfyUI connected"
    : aiMaskCanvas
      ? "AI hook: External AI mask loaded"
      : "AI hook: Not connected — use 'Test Connection' or 'Generate AI Mask'";
```

With:

```js
  const aiLabel = aiMaskCanvas
    ? "AI hook: AI mask loaded"
    : "AI hook: Use 'Generate AI Mask' or 'Load AI Mask PNG'";
```

- [ ] **Step 2: Fix getIdleGuidanceMessage()**

Find the `getIdleGuidanceMessage` function. Replace the `if (bgMode.value === "ai")` block:

```js
  if (bgMode.value === "ai") {
    return comfyuiConnected
      ? `AI mode ready. Click 'Generate AI Mask' to run segmentation via ComfyUI, or 'Load AI Mask PNG' for an external matte. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`
      : `AI mode ready. Click 'Generate AI Mask' to connect to ComfyUI and run segmentation, or 'Load AI Mask PNG' for an external matte. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`;
  }
```

With:

```js
  if (bgMode.value === "ai") {
    return `AI mode ready. Click 'Generate AI Mask' for browser segmentation, or 'Load AI Mask PNG' for an external matte. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`;
  }
```

- [ ] **Step 3: Fix applyPreset()**

Find the `applyPreset` function. Delete these two lines:

```js
  // ComfyUI model selection from preset
  if (preset.comfyui && comfyuiModel) comfyuiModel.value = preset.comfyui.model;
```

- [ ] **Step 4: Fix the drawImagePreservingRGB comment**

Find the comment block above `drawImagePreservingRGB` (search for `ComfyUI outputs masks`). Update the comment:

```js
/**
 * Draw an Image onto a canvas preserving RGB even when alpha=0.
 * ComfyUI outputs masks as RGBA with alpha=0 but data in RGB.
 * Canvas drawImage uses premultiplied alpha, zeroing RGB when alpha=0.
```

Replace with:

```js
/**
 * Draw an Image onto a canvas preserving RGB even when alpha=0.
 * Some mask sources output RGBA with alpha=0 but data in RGB.
 * Canvas drawImage uses premultiplied alpha, zeroing RGB when alpha=0.
```

- [ ] **Step 5: Fix aiRemoveWorkflow() ComfyUI fallback**

Find the block in `aiRemoveWorkflow` that falls back to ComfyUI (search for `Hybrid mask is empty`):

```js
    if (coverage < 0.005) {
      // Hybrid mask is empty — fall back to ComfyUI if connected
      if (comfyuiConnected) {
        if (aiRemoveStatus) aiRemoveStatus.textContent = "Hybrid detection found nothing — trying ComfyUI...";
        await generateComfyuiMask();
        if (!importedAiMaskAlpha) throw new Error("Both hybrid and ComfyUI mask generation failed.");
      } else {
        throw new Error("No UI regions detected. Try adjusting the background tone or using manual tools.");
      }
    }
```

Replace with:

```js
    if (coverage < 0.005) {
      throw new Error("No UI regions detected. Try adjusting the background tone or using manual tools.");
    }
```

- [ ] **Step 6: Fix processBatchImages() ComfyUI path**

Find the `processBatchImages` function. Delete the `modelType` variable declaration:

```js
  const modelType = comfyuiModel ? comfyuiModel.value : "BiRefNet-general";
```

Delete the ComfyUI connection check block:

```js
  if (aiSource === "comfyui") {
    const connected = await testComfyuiConnection();
    if (!connected) {
      if (bgStatus) bgStatus.textContent = "ComfyUI connection failed. Check the server or switch to another mode.";
      return;
    }
  }
```

Replace the ComfyUI branch in the mask generation:

```js
        if (aiSource === "comfyui") {
          maskAlpha = await generateComfyuiMaskForImage(image, modelType);
        } else {
          maskAlpha = await generateBrowserMaskForImage(image);
        }
```

With:

```js
        maskAlpha = await generateBrowserMaskForImage(image);
```

- [ ] **Step 7: Delete Tab 2 event listeners and initialization**

Find and delete the `form.addEventListener("submit"` block:

```js
form.addEventListener("submit", (event) => {
  event.preventDefault();
  refreshOutput(formStateToConfig());
});
```

Delete the `copyJsonButton`, `copyChecklistButton`, `downloadJsonButton`, and `loadDemoButton` event listener blocks:

```js
copyJsonButton.addEventListener("click", () => {
  if (!currentPayload) return;
  copyText(JSON.stringify(currentPayload.workflow, null, 2));
});

copyChecklistButton.addEventListener("click", () => {
  if (!currentPayload) return;
  copyText(currentPayload.installItems.join("\n"));
});

downloadJsonButton.addEventListener("click", () => {
  if (!currentPayload) return;
  const blob = new Blob([JSON.stringify(currentPayload.workflow, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "comfyui-workflow-template.json";
  link.click();
  URL.revokeObjectURL(url);
});

loadDemoButton.addEventListener("click", () => {
  form.workflowType.value = "combined";
  form.artStyle.value = "fantasy";
  form.checkpoint.value = "juggernautXL";
  form.remover.value = "essentials";
  form.assetType.value = "ornate inventory button";
  form.material.value = "ornate gold border, carved stone backing, glowing rune core";
  form.batchMode.checked = false;
  form.pixelEdges.checked = false;
  refreshOutput(formStateToConfig());
});
```

- [ ] **Step 8: Delete ComfyUI event listeners**

Delete:

```js
if (comfyuiConnectButton) {
  comfyuiConnectButton.addEventListener("click", testComfyuiConnection);
}
if (comfyuiGenerateMaskButton) {
  comfyuiGenerateMaskButton.addEventListener("click", generateComfyuiMask);
}
```

- [ ] **Step 9: Fix initialization code**

Delete the `refreshOutput(formStateToConfig());` call from the initialization section at the bottom of app.js.

Delete the auto-connect line:

```js
// Auto-connect to ComfyUI on page load (silent)
testComfyuiConnection().catch(() => {});
```

- [ ] **Step 10: Run syntax check**

Run: `node --check app.js` from the `Image generator` directory.

Expected: No output (clean syntax).

- [ ] **Step 11: Commit**

```bash
git add app.js
git commit -m "refactor: rewire all ComfyUI references — browser ONNX is now primary AI mask path"
```

---

### Task 6: Remove ComfyUI from serve.py

**Files:**
- Modify: `serve.py:1-78` (imports, constants, ComfyUI functions)
- Modify: `serve.py:102-113` (proxy and save-mask handlers)
- Modify: `serve.py:126-213` (`_save_mask` and `_proxy` methods)
- Modify: `serve.py:222,234,248,260-261` (startup code)

- [ ] **Step 1: Update module docstring and remove ComfyUI constants**

Replace lines 1-26:

```python
"""Local HTTP server for the asset editor app.

Run:  python serve.py
Then open:  http://localhost:8080

Serves app files and proxies /comfyui/* requests to ComfyUI
so the browser doesn't hit CORS issues.
Auto-launches ComfyUI desktop app if not already running.
"""

import http.server
import os
import subprocess
import time
import urllib.request
import urllib.error
import json as _json
import threading

PORT = 8080
COMFYUI_PORT = 8000
COMFYUI_BASE = f"http://127.0.0.1:{COMFYUI_PORT}"
COMFYUI_EXE = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\ComfyUI\ComfyUI.exe"
)
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
```

With:

```python
"""Local HTTP server for the Gut It Out asset editor app.

Run:  python serve.py
Then open:  http://localhost:8080

Serves app files and Python API endpoints for extraction,
border detection, mask operations, and image enhancement.
"""

import http.server
import os
import time
import json as _json
import threading

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
```

- [ ] **Step 2: Delete find_comfyui_port and ensure_comfyui_running**

Delete the two functions `find_comfyui_port()` (lines 32-42) and `ensure_comfyui_running()` (lines 44-78).

- [ ] **Step 3: Simplify do_GET — remove comfyui proxy**

In the `do_GET` method, replace:

```python
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._handle_api("GET")
        elif self.path.startswith("/comfyui/"):
            self._proxy("GET")
        else:
            super().do_GET()
```

With:

```python
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._handle_api("GET")
        else:
            super().do_GET()
```

- [ ] **Step 4: Simplify do_POST — remove save-mask and comfyui proxy**

Replace:

```python
    def do_POST(self):
        if self.path.startswith("/api/"):
            self._handle_api("POST")
        elif self.path == "/save-mask":
            self._save_mask()
        elif self.path.startswith("/comfyui/"):
            self._proxy("POST")
        else:
            self.send_response(405)
            self.end_headers()
```

With:

```python
    def do_POST(self):
        if self.path.startswith("/api/"):
            self._handle_api("POST")
        else:
            self.send_response(405)
            self.end_headers()
```

- [ ] **Step 5: Delete _save_mask and _proxy methods**

Delete the entire `_save_mask(self)` method and the entire `_proxy(self, method)` method from the Handler class.

- [ ] **Step 6: Simplify log_message**

Replace:

```python
    def log_message(self, format, *args):
        # Quieter logging - only show errors and proxy requests
        msg = format % args
        if "/api/" in msg or "/comfyui/" in msg or "error" in msg.lower() or "40" in msg or "50" in msg:
            super().log_message(format, *args)
```

With:

```python
    def log_message(self, format, *args):
        msg = format % args
        if "/api/" in msg or "error" in msg.lower() or "40" in msg or "50" in msg:
            super().log_message(format, *args)
```

- [ ] **Step 7: Update startup code**

In the `if __name__ == "__main__":` block:

Remove the `ensure_comfyui_running()` call.

Remove the workflow endpoint import and registration:

```python
    from api.endpoints import workflow as ep_workflow
```

and:

```python
    ep_workflow.register(api_router)
```

Update the startup print messages. Replace:

```python
        print(f"Serving at http://127.0.0.1:{PORT}")
        print(f"API at http://127.0.0.1:{PORT}/api/*")
        print(f"ComfyUI proxy at http://127.0.0.1:{PORT}/comfyui/*")
        print(f"ComfyUI backend: {COMFYUI_BASE}")
        print(f"Directory: {DIRECTORY}")
```

With:

```python
        print(f"Serving at http://127.0.0.1:{PORT}")
        print(f"API at http://127.0.0.1:{PORT}/api/*")
        print(f"Directory: {DIRECTORY}")
```

- [ ] **Step 8: Run syntax check**

Run: `python -m py_compile serve.py` from the `Image generator` directory (using `.venv/Scripts/python.exe`).

Expected: No output (clean syntax).

- [ ] **Step 9: Commit**

```bash
git add serve.py
git commit -m "refactor: remove ComfyUI auto-launch, proxy, and save-mask from serve.py"
```

---

### Task 7: Delete ComfyUI-only files

**Files:**
- Delete: `api/endpoints/workflow.py`
- Delete: `starter-workflow-background-removal-only.json`
- Delete: `starter-workflow-juggernaut-fantasy.json`
- Delete: `starter-workflow-pixel-ui-background-removal.json`

- [ ] **Step 1: Delete workflow endpoint**

```bash
rm api/endpoints/workflow.py
```

- [ ] **Step 2: Delete starter workflow JSON files**

```bash
rm starter-workflow-background-removal-only.json
rm starter-workflow-juggernaut-fantasy.json
rm starter-workflow-pixel-ui-background-removal.json
```

- [ ] **Step 3: Commit**

```bash
git add -u api/endpoints/workflow.py starter-workflow-*.json
git commit -m "refactor: delete ComfyUI workflow endpoint and starter workflow templates"
```

---

### Task 8: Verify everything works

**Files:** None (testing only)

- [ ] **Step 1: Run JS syntax check**

Run: `node --check app.js` from the `Image generator` directory.

Expected: No output (clean syntax).

- [ ] **Step 2: Run Python syntax check**

Run: `.venv/Scripts/python.exe -m py_compile serve.py` from the `Image generator` directory.

Expected: No output (clean syntax).

- [ ] **Step 3: Search for remaining ComfyUI references in app.js**

Run: `grep -in "comfyui\|comfy" app.js`

Expected: Zero matches (or only the `drawImagePreservingRGB` comment which was updated to remove the ComfyUI reference). If any functional references remain, fix them.

- [ ] **Step 4: Search for remaining ComfyUI references in index.html**

Run: `grep -in "comfyui\|comfy" index.html`

Expected: Zero matches.

- [ ] **Step 5: Search for remaining ComfyUI references in serve.py**

Run: `grep -in "comfyui\|comfy" serve.py`

Expected: Zero matches.

- [ ] **Step 6: Start the server and verify it loads**

Run: `.venv/Scripts/python.exe serve.py` from the `Image generator` directory.

Expected: Server starts without errors, prints `Serving at http://127.0.0.1:8080` and `API at http://127.0.0.1:8080/api/*`. No ComfyUI-related messages. No crash.

- [ ] **Step 7: Take a screenshot of the running app**

Run: `python screenshot.py http://127.0.0.1:8080/index.html verify_comfyui_removal.png` from the `Image generator` directory.

Verify: No ComfyUI controls visible. Single-page extraction UI. "Generate AI Mask" button present. No "Workflow Builder" tab.

- [ ] **Step 8: Run existing test suite**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v --ignore=tests/test_production.py -x` from the `Image generator` directory.

Expected: All tests pass. The test suite uses AI Remove and Process Image workflows which are ComfyUI-independent.

- [ ] **Step 9: Commit verification screenshot**

```bash
git add verify_comfyui_removal.png
git commit -m "test: verify ComfyUI removal — app loads cleanly without ComfyUI"
```

---

### Task 9: Update project documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Update CLAUDE.md**

In `CLAUDE.md`, update the Mission section — remove "ComfyUI workflow builder" references if any.

Update the Dev Commands section. Replace:

```markdown
App also opens directly via `index.html` — server only needed for ComfyUI proxy.
```

With:

```markdown
App also opens directly via `index.html` — server needed for Python API endpoints (border detection, extraction).
```

Update the Architecture section. Replace:

```markdown
- **`index.html`** — Two-tab layout: Extraction + Workflow Builder
```

With:

```markdown
- **`index.html`** — Single-page extraction UI
```

Replace:

```markdown
- **`serve.py`** — HTTP server + CORS proxy + `/save-mask`
```

With:

```markdown
- **`serve.py`** — HTTP server + Python API endpoints
```

- [ ] **Step 2: Update README.md**

Update `README.md` to remove any ComfyUI references. Change the title/description from "ComfyUI Asset Editor Builder" to "Gut It Out — UI Asset and Object Extractor" if it still has the old name. Remove ComfyUI setup instructions.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: update project docs to reflect ComfyUI removal"
```
