# API Automation Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a REST API layer (`/api/*`) to serve.py that exposes all app functionality programmatically, using Playwright headless browsers to execute the existing app.js logic.

**Architecture:** serve.py gains an API router that dispatches `/api/*` requests to endpoint handlers. Long-running jobs (extraction, batch, mask generation) run in background threads using a Playwright session pool — headless Chromium instances pre-loaded with the app. Results are saved to `output/` and retrievable via job status polling.

**Tech Stack:** Python 3.12, http.server (stdlib), threading (stdlib), playwright (already installed), json/os/time/uuid (stdlib). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-03-28-api-automation-design.md`

---

## File Structure

```
api/
├── __init__.py          — Package init, version constant
├── jobs.py              — Job queue: create, update, get, expire (thread-safe)
├── pool.py              — Playwright session pool: init, checkout, checkin, reset
├── bridge.py            — Playwright ↔ app.js commands: load image, run extraction, read results
├── router.py            — URL dispatch: parse /api/* paths, call endpoint handlers, format responses
└── endpoints/
    ├── __init__.py      — Package init
    ├── extract.py       — POST /api/extract, POST /api/batch, GET /api/status/:id
    ├── config.py        — GET /api/presets, POST /api/preset, GET /api/comfyui/status
    ├── mask.py          — POST /api/mask/generate, POST /api/mask/refine
    ├── enhance.py       — POST /api/enhance
    ├── split.py         — POST /api/split
    └── workflow.py      — POST /api/workflow/build, GET /api/workflow/templates
serve.py                 — Modify: add API dispatch in Handler.do_GET/do_POST, pool startup
tests/
└── test_api.py          — End-to-end API tests using urllib
```

---

### Task 1: Job Manager (`api/jobs.py`)

The foundation — all async endpoints depend on this. Pure Python, no Playwright needed.

**Files:**
- Create: `api/__init__.py`
- Create: `api/jobs.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Create package init**

```python
# api/__init__.py
"""REST API automation layer for the asset editor app."""
API_VERSION = "1.0.0"
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_api.py
"""API automation layer tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.jobs import JobManager

def test_create_job():
    jm = JobManager()
    job_id = jm.create("extract", {"image": "test.png"})
    assert job_id.startswith("extract_")
    job = jm.get(job_id)
    assert job["status"] == "queued"
    assert job["params"]["image"] == "test.png"

def test_update_job_status():
    jm = JobManager()
    job_id = jm.create("extract", {})
    jm.update(job_id, status="processing", progress=0.5, step="Generating mask...")
    job = jm.get(job_id)
    assert job["status"] == "processing"
    assert job["progress"] == 0.5
    assert job["step"] == "Generating mask..."

def test_complete_job():
    jm = JobManager()
    job_id = jm.create("extract", {})
    jm.update(job_id, status="completed", results={"sheet": "output/test.png"})
    job = jm.get(job_id)
    assert job["status"] == "completed"
    assert job["results"]["sheet"] == "output/test.png"
    assert job["elapsed_ms"] >= 0

def test_fail_job():
    jm = JobManager()
    job_id = jm.create("extract", {})
    jm.update(job_id, status="failed", error="ComfyUI disconnected", code="COMFYUI_DISCONNECTED")
    job = jm.get(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "ComfyUI disconnected"

def test_job_not_found():
    jm = JobManager()
    job = jm.get("nonexistent_123")
    assert job is None

def test_expire_old_jobs():
    jm = JobManager(expire_seconds=0)
    job_id = jm.create("extract", {})
    import time; time.sleep(0.01)
    jm.cleanup()
    assert jm.get(job_id) is None

if __name__ == "__main__":
    test_create_job(); print("  PASS: create_job")
    test_update_job_status(); print("  PASS: update_job_status")
    test_complete_job(); print("  PASS: complete_job")
    test_fail_job(); print("  PASS: fail_job")
    test_job_not_found(); print("  PASS: job_not_found")
    test_expire_old_jobs(); print("  PASS: expire_old_jobs")
    print("All job manager tests passed!")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: `ModuleNotFoundError: No module named 'api.jobs'`

- [ ] **Step 4: Implement JobManager**

```python
# api/jobs.py
"""Thread-safe job queue with status tracking and expiration."""
import threading
import time
import uuid


class JobManager:
    def __init__(self, expire_seconds=3600):
        self._jobs = {}
        self._lock = threading.Lock()
        self._counter = 0
        self._expire_seconds = expire_seconds

    def create(self, job_type, params):
        with self._lock:
            self._counter += 1
            job_id = f"{job_type}_{int(time.time())}_{self._counter:03d}"
            self._jobs[job_id] = {
                "job_id": job_id,
                "type": job_type,
                "status": "queued",
                "progress": 0.0,
                "step": "",
                "params": params,
                "results": None,
                "error": None,
                "code": None,
                "created_at": time.time(),
                "started_at": None,
                "completed_at": None,
            }
            return job_id

    def get(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            result = dict(job)
            if result["completed_at"] and result["started_at"]:
                result["elapsed_ms"] = int((result["completed_at"] - result["started_at"]) * 1000)
            elif result["started_at"]:
                result["elapsed_ms"] = int((time.time() - result["started_at"]) * 1000)
            else:
                result["elapsed_ms"] = 0
            return result

    def update(self, job_id, **kwargs):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in kwargs.items():
                if key in job:
                    job[key] = value
            if kwargs.get("status") == "processing" and job["started_at"] is None:
                job["started_at"] = time.time()
            if kwargs.get("status") in ("completed", "failed"):
                job["completed_at"] = time.time()

    def cleanup(self):
        with self._lock:
            now = time.time()
            expired = [
                jid for jid, j in self._jobs.items()
                if now - j["created_at"] > self._expire_seconds
            ]
            for jid in expired:
                del self._jobs[jid]

    def list_jobs(self):
        with self._lock:
            return [dict(j) for j in self._jobs.values()]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: All 6 tests pass.

- [ ] **Step 6: Commit**

```bash
git add api/__init__.py api/jobs.py tests/test_api.py
git commit -m "feat: add job manager for API automation layer"
```

---

### Task 2: Playwright Session Pool (`api/pool.py`)

Manages headless browser workers that execute app.js. Each worker is a Chromium page pre-loaded with the app.

**Files:**
- Create: `api/pool.py`
- Modify: `tests/test_api.py` (add pool tests)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
from api.pool import PlaywrightPool

def test_pool_init_and_checkout():
    pool = PlaywrightPool("http://127.0.0.1:8080", size=1)
    try:
        pool.start()
        page = pool.checkout(timeout=10)
        assert page is not None
        # Verify app loaded
        title = page.title()
        assert "Asset" in title or "Game" in title
        pool.checkin(page)
    finally:
        pool.stop()

def test_pool_checkout_blocks_when_empty():
    pool = PlaywrightPool("http://127.0.0.1:8080", size=1)
    try:
        pool.start()
        page1 = pool.checkout(timeout=5)
        # Second checkout should timeout since pool size is 1
        import time
        start = time.time()
        page2 = pool.checkout(timeout=1)
        elapsed = time.time() - start
        assert page2 is None  # timed out
        assert elapsed >= 0.9
        pool.checkin(page1)
    finally:
        pool.stop()
```

Add to the `if __name__` block:

```python
    # Pool tests require serve.py running
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:8080/", timeout=2)
        test_pool_init_and_checkout(); print("  PASS: pool_init_and_checkout")
        test_pool_checkout_blocks_when_empty(); print("  PASS: pool_checkout_blocks")
    except Exception:
        print("  SKIP: pool tests (serve.py not running)")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: `ModuleNotFoundError: No module named 'api.pool'`

- [ ] **Step 3: Implement PlaywrightPool**

```python
# api/pool.py
"""Playwright session pool — manages headless browser workers."""
import queue
import threading
from playwright.sync_api import sync_playwright


class PlaywrightPool:
    def __init__(self, app_url, size=2):
        self._app_url = app_url
        self._size = size
        self._pool = queue.Queue(maxsize=size)
        self._playwright = None
        self._browser = None
        self._pages = []
        self._lock = threading.Lock()
        self._started = False

    def start(self):
        with self._lock:
            if self._started:
                return
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            for _ in range(self._size):
                context = self._browser.new_context(viewport={"width": 1600, "height": 1200})
                page = context.new_page()
                page.goto(self._app_url, wait_until="networkidle")
                page.wait_for_timeout(1000)
                self._pages.append(page)
                self._pool.put(page)
            self._started = True

    def checkout(self, timeout=30):
        try:
            return self._pool.get(timeout=timeout)
        except queue.Empty:
            return None

    def checkin(self, page):
        self._pool.put(page)

    def reset_page(self, page):
        page.goto(self._app_url, wait_until="networkidle")
        page.wait_for_timeout(500)

    def stop(self):
        with self._lock:
            if not self._started:
                return
            for page in self._pages:
                try:
                    page.context.close()
                except Exception:
                    pass
            self._pages.clear()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            self._started = False

    @property
    def available(self):
        return self._pool.qsize()

    @property
    def total(self):
        return self._size
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: All tests pass (pool tests pass if serve.py is running, skip otherwise).

- [ ] **Step 5: Commit**

```bash
git add api/pool.py tests/test_api.py
git commit -m "feat: add Playwright session pool for headless browser workers"
```

---

### Task 3: App Bridge (`api/bridge.py`)

The core translation layer: converts API parameters into page.evaluate() calls against app.js. This is the largest and most critical file.

**Files:**
- Create: `api/bridge.py`
- Modify: `tests/test_api.py` (add bridge tests)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
from api.bridge import AppBridge

def test_bridge_load_image(pool_page):
    bridge = AppBridge()
    result = bridge.load_image(pool_page, os.path.join(os.path.dirname(__file__), "..", "input", "UI2.1.png"))
    assert result["loaded"]
    assert result["width"] > 0
    assert result["height"] > 0

def test_bridge_apply_preset(pool_page):
    bridge = AppBridge()
    bridge.apply_preset(pool_page, "light-balanced")
    settings = bridge.get_current_settings(pool_page)
    assert settings["threshold"] == 12
    assert settings["tone"] == "light"

def test_bridge_get_comfyui_status(pool_page):
    bridge = AppBridge()
    status = bridge.get_comfyui_status(pool_page)
    assert "connected" in status
```

Add a pool_page helper and update `if __name__`:

```python
def _get_pool_page():
    """Helper: get a pool page for testing."""
    pool = PlaywrightPool("http://127.0.0.1:8080", size=1)
    pool.start()
    page = pool.checkout(timeout=10)
    return pool, page

# In if __name__ block, after pool tests:
    try:
        pool, page = _get_pool_page()
        test_bridge_load_image(page); print("  PASS: bridge_load_image")
        pool.reset_page(page)
        test_bridge_apply_preset(page); print("  PASS: bridge_apply_preset")
        pool.reset_page(page)
        test_bridge_get_comfyui_status(page); print("  PASS: bridge_get_comfyui_status")
        pool.checkin(page)
        pool.stop()
    except Exception as e:
        print(f"  BRIDGE TEST ERROR: {e}")
        try: pool.stop()
        except: pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: `ModuleNotFoundError: No module named 'api.bridge'`

- [ ] **Step 3: Implement AppBridge**

```python
# api/bridge.py
"""Playwright <-> app.js command bridge.

Translates API parameters into page.evaluate() calls that drive the
existing app.js logic in a headless browser.
"""
import base64
import os
import time


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppBridge:
    """Drives the asset editor app via Playwright page.evaluate()."""

    def load_image(self, page, image_path):
        """Load an image into the app via file chooser."""
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Image not found: {abs_path}")
        with page.expect_file_chooser() as fc:
            page.click("#bgInputFile")
        fc.value.set_files(abs_path)
        page.wait_for_timeout(2000)
        return page.evaluate("""() => ({
            loaded: !!loadedImage,
            width: loadedImage ? loadedImage.width : 0,
            height: loadedImage ? loadedImage.height : 0,
            fileName: loadedFileName || ""
        })""")

    def load_image_base64(self, page, data_url):
        """Load a base64-encoded image into the app."""
        page.evaluate("""(dataUrl) => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => {
                    loadedImage = img;
                    loadedFileName = "api_input.png";
                    const c = document.createElement("canvas");
                    c.width = img.width; c.height = img.height;
                    c.getContext("2d").drawImage(img, 0, 0);
                    const oc = document.querySelector("#originalCanvas");
                    if (oc) {
                        oc.width = img.width; oc.height = img.height;
                        oc.getContext("2d").drawImage(img, 0, 0);
                    }
                    resolve(true);
                };
                img.onerror = () => reject("Failed to load base64 image");
                img.src = dataUrl;
            });
        }""", data_url)
        page.wait_for_timeout(500)
        return page.evaluate("() => ({ loaded: !!loadedImage, width: loadedImage?.width || 0, height: loadedImage?.height || 0 })")

    def apply_preset(self, page, preset_name):
        """Select and apply a preset."""
        page.evaluate("() => document.querySelector('.card.closed')?.classList.remove('closed')")
        page.evaluate(f"""(name) => {{
            const sel = document.querySelector('#bgPreset');
            if (sel) {{ sel.value = name; sel.dispatchEvent(new Event('change')); }}
        }}""", preset_name)
        page.wait_for_timeout(300)

    def apply_settings_override(self, page, overrides):
        """Apply individual setting overrides on top of current preset."""
        control_map = {
            "threshold": ("#bgThreshold", "value"),
            "softness": ("#bgSoftness", "value"),
            "alphaFloor": ("#bgAlphaFloor", "value"),
            "alphaCeiling": ("#bgAlphaCeiling", "value"),
            "edgeCleanupStrength": ("#bgEdgeCleanupStrength", "value"),
            "componentAlpha": ("#bgComponentAlpha", "value"),
            "componentPixels": ("#bgComponentPixels", "value"),
            "componentPad": ("#bgComponentPad", "value"),
            "objectPad": ("#bgObjectPad", "value"),
            "tone": ("#bgTone", "value"),
            "decontaminate": ("#bgDecontaminate", "checked"),
            "cropTransparent": ("#bgCropTransparent", "checked"),
            "strongBorderRepair": ("#bgStrongBorderRepair", "checked"),
            "preserveColor": ("#bgPreserveColor", "checked"),
            "secondPass": ("#bgSecondPass", "checked"),
            "aiConfidence": ("#bgAiConfidence", "value"),
            "aiMatte": ("#bgAiMatte", "value"),
            "aiSpill": ("#bgAiSpill", "value"),
            "aiInvertMask": ("#bgAiInvertMask", "checked"),
            "aiMaskExpand": ("#bgAiMaskExpand", "value"),
            "aiMaskFeather": ("#bgAiMaskFeather", "value"),
        }
        for key, val in overrides.items():
            if key in control_map:
                selector, prop = control_map[key]
                if prop == "checked":
                    page.evaluate(f"() => {{ const el = document.querySelector('{selector}'); if (el) el.checked = {str(val).lower()}; }}")
                else:
                    page.evaluate(f"(v) => {{ const el = document.querySelector('{selector}'); if (el) el.value = String(v); }}", val)
        page.evaluate("() => { if (typeof updateRangeLabels === 'function') updateRangeLabels(); }")

    def get_current_settings(self, page):
        """Read current settings from the app."""
        return page.evaluate("() => getBgSettings()")

    def run_ai_remove(self, page, on_progress=None, timeout_s=120):
        """Click AI Remove and wait for completion."""
        page.click("#aiRemoveButton")
        start = time.time()
        while time.time() - start < timeout_s:
            time.sleep(1)
            status = page.evaluate('() => document.querySelector("#aiRemoveStatus")?.textContent || ""')
            if on_progress:
                elapsed = time.time() - start
                if "Step 1" in status:
                    on_progress(0.3, status)
                elif "Step 2" in status:
                    on_progress(0.7, status)
            if "Done" in status:
                return {"ok": True, "status": status}
            if "failed" in status or "error" in status.lower():
                return {"ok": False, "status": status, "error": status}
        return {"ok": False, "status": "timeout", "error": f"AI Remove timed out after {timeout_s}s"}

    def run_process_image(self, page, on_progress=None, timeout_s=120):
        """Click Process Image and wait for completion."""
        page.click("#processBgButton")
        start = time.time()
        while time.time() - start < timeout_s:
            time.sleep(1)
            status = page.evaluate('() => document.querySelector("#bgStatus")?.textContent || ""')
            btn_disabled = page.evaluate('() => document.querySelector("#processBgButton")?.disabled')
            if on_progress:
                on_progress(0.5, status)
            if not btn_disabled and time.time() - start > 2:
                return {"ok": True, "status": status}
            if "error" in status.lower():
                return {"ok": False, "status": status, "error": status}
        return {"ok": False, "status": "timeout", "error": f"Process timed out after {timeout_s}s"}

    def run_enhance(self, page):
        """Click AI Enhance and wait for result."""
        btn = page.query_selector("#aiEnhanceButton")
        if not btn:
            return {"ok": False, "error": "AI Enhance button not found"}
        btn.click()
        page.wait_for_timeout(3000)
        status = page.evaluate('() => document.querySelector("#aiEnhanceStatus")?.textContent || ""')
        has_result = page.evaluate('() => { const c = document.querySelector("#aiEnhancedCanvas"); return c && c.width > 1; }')
        return {"ok": has_result, "status": status}

    def generate_mask_only(self, page, on_progress=None, timeout_s=120):
        """Generate ComfyUI mask without running extraction."""
        page.click("#comfyuiGenerateMaskButton")
        start = time.time()
        while time.time() - start < timeout_s:
            time.sleep(1)
            status = page.evaluate('() => document.querySelector("#comfyuiStatus")?.textContent || ""')
            if "mask generated" in status.lower():
                coverage = page.evaluate("""() => {
                    if (!importedAiMaskAlpha) return 0;
                    let fg = 0;
                    for (let i = 0; i < importedAiMaskAlpha.length; i++) {
                        if (importedAiMaskAlpha[i] > 128) fg++;
                    }
                    return fg / importedAiMaskAlpha.length;
                }""")
                inverted = "auto-inverted" in status
                return {"ok": True, "status": status, "coverage": coverage, "auto_inverted": inverted}
            if "error" in status.lower():
                return {"ok": False, "status": status, "error": status}
        return {"ok": False, "error": f"Mask generation timed out after {timeout_s}s"}

    def extract_alpha_stats(self, page, canvas_id="aiFinalCanvas"):
        """Read alpha channel statistics from a canvas."""
        return page.evaluate(f"""() => {{
            const c = document.querySelector('#{canvas_id}');
            if (!c || c.width <= 1) return null;
            const ctx = c.getContext('2d');
            const d = ctx.getImageData(0, 0, c.width, c.height);
            let transparent = 0, opaque = 0, semi = 0;
            for (let i = 3; i < d.data.length; i += 4) {{
                if (d.data[i] === 0) transparent++;
                else if (d.data[i] === 255) opaque++;
                else semi++;
            }}
            const total = transparent + opaque + semi;
            return {{
                transparent: Math.round(transparent / total * 1000) / 10,
                semi: Math.round(semi / total * 1000) / 10,
                opaque: Math.round(opaque / total * 1000) / 10,
                total: total
            }};
        }}""")

    def save_canvas_to_file(self, page, canvas_id, output_path):
        """Extract canvas data and save as PNG file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        data_url = page.evaluate(f"""() => {{
            const c = document.querySelector('#{canvas_id}');
            return c && c.width > 1 ? c.toDataURL('image/png') : null;
        }}""")
        if not data_url:
            return None
        raw = base64.b64decode(data_url.split(",", 1)[1])
        with open(output_path, "wb") as f:
            f.write(raw)
        return {"file": output_path, "size": len(raw)}

    def extract_all_results(self, page, output_dir, base_name="result"):
        """Extract all available result canvases and save to output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        results = {}
        canvas_map = {
            "sheet": ("processedLayoutCanvas", f"{base_name}_sheet.png"),
            "final": ("aiFinalCanvas", f"{base_name}_final.png"),
            "enhanced": ("aiEnhancedCanvas", f"{base_name}_enhanced.png"),
        }
        # Check which canvases exist using JS global variables
        existing = page.evaluate("""() => ({
            processedLayoutCanvas: typeof processedLayoutCanvas !== 'undefined' && processedLayoutCanvas && processedLayoutCanvas.width > 1,
            aiFinalCanvas: !!document.querySelector('#aiFinalCanvas') && document.querySelector('#aiFinalCanvas').width > 1,
            aiEnhancedCanvas: !!document.querySelector('#aiEnhancedCanvas') && document.querySelector('#aiEnhancedCanvas').width > 1
        })""")
        # Save the sheet from the JS variable (not a DOM canvas)
        if existing.get("processedLayoutCanvas"):
            data_url = page.evaluate("""() => {
                if (typeof processedLayoutCanvas === 'undefined' || !processedLayoutCanvas) return null;
                return processedLayoutCanvas.toDataURL('image/png');
            }""")
            if data_url:
                raw = base64.b64decode(data_url.split(",", 1)[1])
                path = os.path.join(output_dir, f"{base_name}_sheet.png")
                with open(path, "wb") as f:
                    f.write(raw)
                results["sheet"] = path
        # Save DOM canvases
        for key in ("final", "enhanced"):
            canvas_var, filename = canvas_map[key]
            if existing.get(canvas_var):
                saved = self.save_canvas_to_file(page, canvas_var, os.path.join(output_dir, filename))
                if saved:
                    results[key] = saved["file"]
        # Save mask
        mask_data = page.evaluate("""() => {
            if (typeof aiMaskCanvas !== 'undefined' && aiMaskCanvas && aiMaskCanvas.width > 1) {
                return aiMaskCanvas.toDataURL('image/png');
            }
            return null;
        }""")
        if mask_data:
            raw = base64.b64decode(mask_data.split(",", 1)[1])
            path = os.path.join(output_dir, f"{base_name}_mask.png")
            with open(path, "wb") as f:
                f.write(raw)
            results["mask"] = path
        # Extract panels
        panels = self.extract_panels(page, output_dir, base_name)
        if panels:
            results["panels"] = panels
        # Alpha stats
        alpha = self.extract_alpha_stats(page)
        if alpha:
            results["alpha_stats"] = alpha
        return results

    def extract_panels(self, page, output_dir, base_name="result"):
        """Extract split panel data and save each panel."""
        panel_info = page.evaluate("""() => {
            if (typeof processedPanels === 'undefined' || !processedPanels || !processedPanels.length) return [];
            return processedPanels.map((p, i) => ({
                index: i,
                width: p.canvas ? p.canvas.width : 0,
                height: p.canvas ? p.canvas.height : 0,
                score: p.score || 0,
                dataUrl: p.canvas && p.canvas.width > 1 ? p.canvas.toDataURL('image/png') : null
            }));
        }""")
        panels = []
        for p in panel_info:
            if p.get("dataUrl"):
                filename = f"{base_name}_panel_{p['index']+1:02d}.png"
                path = os.path.join(output_dir, filename)
                raw = base64.b64decode(p["dataUrl"].split(",", 1)[1])
                with open(path, "wb") as f:
                    f.write(raw)
                panels.append({
                    "index": p["index"],
                    "file": path,
                    "width": p["width"],
                    "height": p["height"],
                    "score": p["score"]
                })
        return panels

    def get_comfyui_status(self, page):
        """Read ComfyUI connection status from the app."""
        return page.evaluate("""() => {
            const el = document.querySelector('#comfyuiStatus');
            return el ? el.textContent : 'unknown';
        }""")

    def get_presets(self, page):
        """Read all available presets from app.js."""
        return page.evaluate("() => JSON.parse(JSON.stringify(bgPresets))")

    def build_workflow(self, page, config):
        """Fill workflow builder form and extract generated JSON."""
        page.evaluate("""(cfg) => {
            const form = document.querySelector('#workflowForm');
            if (!form) return;
            if (cfg.workflow_type) form.workflowType.value = cfg.workflow_type;
            if (cfg.art_style) form.style.value = cfg.art_style;
            if (cfg.checkpoint) form.checkpoint.value = cfg.checkpoint;
            if (cfg.remover) form.remover.value = cfg.remover;
            if (cfg.asset_type) form.assetType.value = cfg.asset_type;
            if (cfg.material) form.material.value = cfg.material;
            if (cfg.batch_mode !== undefined) form.batchMode.checked = cfg.batch_mode;
            if (cfg.pixel_edges !== undefined) form.pixelEdges.checked = cfg.pixel_edges;
            // Trigger refresh
            form.dispatchEvent(new Event('change'));
        }""", config)
        page.wait_for_timeout(500)
        return page.evaluate("""() => {
            const wj = document.querySelector('#workflowJson');
            const pp = document.querySelector('#positivePrompt');
            const np = document.querySelector('#negativePrompt');
            try {
                return {
                    workflow: JSON.parse(wj?.value || '{}'),
                    prompts: {
                        positive: pp?.value || '',
                        negative: np?.value || ''
                    }
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: All tests pass (bridge tests pass if serve.py is running).

- [ ] **Step 5: Commit**

```bash
git add api/bridge.py tests/test_api.py
git commit -m "feat: add Playwright-to-app.js bridge for API automation"
```

---

### Task 4: API Router (`api/router.py`)

Dispatches `/api/*` requests to endpoint handlers. Handles JSON parsing, error formatting, and CORS.

**Files:**
- Create: `api/router.py`

- [ ] **Step 1: Implement the router**

```python
# api/router.py
"""URL routing and request handling for /api/* endpoints."""
import json
import traceback


class APIRouter:
    def __init__(self, job_manager, pool, bridge):
        self.jobs = job_manager
        self.pool = pool
        self.bridge = bridge
        self._routes_get = {}
        self._routes_post = {}
        self._custom_presets = {}

    def register_get(self, path, handler):
        self._routes_get[path] = handler

    def register_post(self, path, handler):
        self._routes_post[path] = handler

    def handle_request(self, handler, method, path, body=None):
        """Dispatch a request. Returns (status_code, response_dict)."""
        # Clean path
        path = path.split("?")[0].rstrip("/")

        # Parse JSON body for POST
        params = {}
        if body and method == "POST":
            try:
                params = json.loads(body) if body else {}
            except json.JSONDecodeError:
                return 400, {"error": "Invalid JSON body", "code": "BAD_REQUEST"}

        # Match route
        routes = self._routes_get if method == "GET" else self._routes_post
        # Try exact match first
        if path in routes:
            try:
                return routes[path](params)
            except Exception as e:
                traceback.print_exc()
                return 500, {"error": str(e), "code": "INTERNAL_ERROR"}

        # Try prefix match for parameterized routes (e.g., /api/status/:id)
        for route_path, route_handler in routes.items():
            if ":id" in route_path:
                prefix = route_path.split(":id")[0]
                if path.startswith(prefix) and len(path) > len(prefix):
                    param_value = path[len(prefix):]
                    params["_id"] = param_value
                    try:
                        return route_handler(params)
                    except Exception as e:
                        traceback.print_exc()
                        return 500, {"error": str(e), "code": "INTERNAL_ERROR"}

        return 404, {"error": f"Unknown API endpoint: {path}", "code": "NOT_FOUND"}

    def send_json(self, handler, status_code, data):
        """Write a JSON response to the HTTP handler."""
        body = json.dumps(data).encode()
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
```

- [ ] **Step 2: Verify syntax**

Run: `.venv/Scripts/python.exe -c "import api.router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add api/router.py
git commit -m "feat: add API router for /api/* request dispatch"
```

---

### Task 5: Endpoint Handlers — Extract & Status (`api/endpoints/extract.py`)

The core extraction endpoints. Uses bridge + pool + jobs.

**Files:**
- Create: `api/endpoints/__init__.py`
- Create: `api/endpoints/extract.py`

- [ ] **Step 1: Create package init**

```python
# api/endpoints/__init__.py
"""API endpoint handlers."""
```

- [ ] **Step 2: Implement extract endpoints**

```python
# api/endpoints/extract.py
"""Extraction endpoints: POST /api/extract, POST /api/batch, GET /api/status/:id"""
import os
import threading


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):
    """Register extraction endpoints on the router."""

    def handle_extract(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        preset = params.get("preset", "dark-balanced")
        if preset not in router.bridge.get_presets_cached() and preset not in router._custom_presets:
            return 400, {"error": f"Unknown preset: {preset}", "code": "INVALID_PRESET"}
        mode = params.get("mode", "ai-remove")
        output_dir = params.get("output_dir", "output")
        settings_override = params.get("settings_override", {})

        job_id = router.jobs.create("extract", {
            "image": image, "preset": preset, "mode": mode,
            "output_dir": output_dir, "settings_override": settings_override
        })
        thread = threading.Thread(
            target=_run_extract_job,
            args=(router, job_id, image, preset, mode, output_dir, settings_override),
            daemon=True
        )
        thread.start()
        return 202, {"job_id": job_id, "status": "queued"}

    def handle_batch(params):
        images = params.get("images", [])
        if not images:
            return 400, {"error": "Missing required field: images", "code": "NO_IMAGE"}
        preset = params.get("preset", "dark-balanced")
        mode = params.get("mode", "ai-remove")
        ai_source = params.get("ai_source", "comfyui")
        output_dir = params.get("output_dir", "output/batch")

        job_id = router.jobs.create("batch", {
            "images": images, "preset": preset, "mode": mode,
            "ai_source": ai_source, "output_dir": output_dir, "total": len(images)
        })
        thread = threading.Thread(
            target=_run_batch_job,
            args=(router, job_id, images, preset, mode, ai_source, output_dir),
            daemon=True
        )
        thread.start()
        return 202, {"job_id": job_id, "status": "queued", "total": len(images)}

    def handle_status(params):
        job_id = params.get("_id", "")
        job = router.jobs.get(job_id)
        if not job:
            return 404, {"error": f"Job not found: {job_id}", "code": "JOB_NOT_FOUND"}
        # Clean up internal fields
        response = {
            "job_id": job["job_id"],
            "status": job["status"],
            "progress": job["progress"],
            "step": job["step"],
            "elapsed_ms": job.get("elapsed_ms", 0),
        }
        if job["status"] == "completed":
            response["results"] = job["results"]
        if job["status"] == "failed":
            response["error"] = job["error"]
            response["code"] = job["code"]
        if job["type"] == "batch":
            response["total"] = job["params"].get("total", 0)
            if job.get("results") and "completed_images" in job["results"]:
                response["completed_images"] = job["results"]["completed_images"]
        return 200, response

    router.register_post("/api/extract", handle_extract)
    router.register_post("/api/batch", handle_batch)
    router.register_get("/api/status/:id", handle_status)


def _resolve_image_path(image):
    """Resolve image path — support relative paths and absolute paths."""
    if image.startswith("data:"):
        return image  # base64
    if os.path.isabs(image):
        return image
    return os.path.join(PROJECT_DIR, image)


def _run_extract_job(router, job_id, image, preset, mode, output_dir, settings_override):
    """Run extraction in a background thread using a pooled browser page."""
    router.jobs.update(job_id, status="processing", progress=0.1, step="Acquiring browser worker...")
    page = router.pool.checkout(timeout=30)
    if page is None:
        router.jobs.update(job_id, status="failed", error="All browser workers busy", code="POOL_EXHAUSTED")
        return
    try:
        router.pool.reset_page(page)
        router.jobs.update(job_id, progress=0.15, step="Loading image...")

        image_path = _resolve_image_path(image)
        if image_path.startswith("data:"):
            load_result = router.bridge.load_image_base64(page, image_path)
        else:
            load_result = router.bridge.load_image(page, image_path)
        if not load_result.get("loaded"):
            router.jobs.update(job_id, status="failed", error="Failed to load image", code="LOAD_FAILED")
            return

        router.jobs.update(job_id, progress=0.2, step="Applying preset...")
        router.bridge.apply_preset(page, preset)
        if settings_override:
            router.bridge.apply_settings_override(page, settings_override)

        def on_progress(pct, step):
            router.jobs.update(job_id, progress=0.2 + pct * 0.6, step=step)

        abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
        os.makedirs(abs_output, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image if not image.startswith("data:") else "api_input.png"))[0]

        if mode == "ai-remove":
            router.jobs.update(job_id, progress=0.25, step="Running AI Remove...")
            result = router.bridge.run_ai_remove(page, on_progress=on_progress)
        elif mode == "heuristic":
            router.jobs.update(job_id, progress=0.25, step="Running heuristic extraction...")
            result = router.bridge.run_process_image(page, on_progress=on_progress)
        elif mode == "crop":
            page.evaluate("() => { document.querySelector('#bgMode').value = 'crop'; document.querySelector('#bgMode').dispatchEvent(new Event('change')); }")
            result = router.bridge.run_process_image(page, on_progress=on_progress)
        else:
            router.jobs.update(job_id, status="failed", error=f"Unknown mode: {mode}", code="BAD_REQUEST")
            return

        if not result.get("ok"):
            router.jobs.update(job_id, status="failed", error=result.get("error", "Extraction failed"), code="EXTRACTION_FAILED")
            return

        router.jobs.update(job_id, progress=0.85, step="Extracting results...")

        # Run enhance if AI Remove was used
        if mode == "ai-remove":
            router.bridge.run_enhance(page)

        results = router.bridge.extract_all_results(page, abs_output, base_name)
        router.jobs.update(job_id, status="completed", progress=1.0, step="Done", results=results)

    except Exception as e:
        router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
    finally:
        router.pool.checkin(page)


def _run_batch_job(router, job_id, images, preset, mode, ai_source, output_dir):
    """Run batch extraction in a background thread."""
    router.jobs.update(job_id, status="processing", progress=0.0, step="Starting batch...")
    page = router.pool.checkout(timeout=30)
    if page is None:
        router.jobs.update(job_id, status="failed", error="All browser workers busy", code="POOL_EXHAUSTED")
        return
    try:
        abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
        os.makedirs(abs_output, exist_ok=True)
        completed = []
        per_image_results = {}
        total = len(images)

        for idx, image in enumerate(images):
            router.pool.reset_page(page)
            pct = idx / total
            router.jobs.update(job_id, progress=pct, step=f"Processing {idx+1}/{total}: {os.path.basename(image)}")

            try:
                image_path = _resolve_image_path(image)
                load_result = router.bridge.load_image(page, image_path)
                if not load_result.get("loaded"):
                    per_image_results[image] = {"error": "Failed to load"}
                    continue

                router.bridge.apply_preset(page, preset)

                if mode == "ai-remove":
                    result = router.bridge.run_ai_remove(page)
                else:
                    result = router.bridge.run_process_image(page)

                if result.get("ok"):
                    base_name = os.path.splitext(os.path.basename(image))[0]
                    img_results = router.bridge.extract_all_results(page, abs_output, base_name)
                    per_image_results[image] = img_results
                    completed.append(image)
                else:
                    per_image_results[image] = {"error": result.get("error", "Failed")}
            except Exception as e:
                per_image_results[image] = {"error": str(e)}

        router.jobs.update(job_id, status="completed", progress=1.0,
                           step=f"Batch complete: {len(completed)}/{total}",
                           results={"completed_images": completed, "per_image": per_image_results})
    except Exception as e:
        router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
    finally:
        router.pool.checkin(page)
```

- [ ] **Step 3: Verify syntax**

Run: `.venv/Scripts/python.exe -c "import api.endpoints.extract; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add api/endpoints/__init__.py api/endpoints/extract.py
git commit -m "feat: add extract and batch API endpoints"
```

---

### Task 6: Endpoint Handlers — Config (`api/endpoints/config.py`)

Presets, custom presets, ComfyUI status.

**Files:**
- Create: `api/endpoints/config.py`

- [ ] **Step 1: Implement config endpoints**

```python
# api/endpoints/config.py
"""Configuration endpoints: GET /api/presets, POST /api/preset, GET /api/comfyui/status"""
import json
import urllib.request
import urllib.error


def register(router):
    """Register configuration endpoints."""

    # Cache presets from app.js on first call
    _presets_cache = {"data": None}

    def _get_presets():
        if _presets_cache["data"] is None:
            page = router.pool.checkout(timeout=10)
            if page:
                try:
                    _presets_cache["data"] = router.bridge.get_presets(page)
                finally:
                    router.pool.checkin(page)
        return _presets_cache["data"] or {}

    # Attach to bridge for use by extract endpoint validation
    router.bridge.get_presets_cached = _get_presets

    def handle_get_presets(params):
        presets = _get_presets()
        combined = {**presets, **router._custom_presets}
        return 200, {"presets": combined, "default": "dark-balanced"}

    def handle_create_preset(params):
        name = params.get("name")
        settings = params.get("settings")
        if not name:
            return 400, {"error": "Missing required field: name", "code": "BAD_REQUEST"}
        if not settings:
            return 400, {"error": "Missing required field: settings", "code": "BAD_REQUEST"}
        router._custom_presets[name] = settings
        return 200, {"ok": True, "name": name}

    def handle_comfyui_status(params):
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/system_stats")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                system = data.get("system", {})
                devices = data.get("devices", [{}])
                gpu_name = devices[0].get("name", "unknown") if devices else "unknown"
                return 200, {
                    "connected": True,
                    "port": 8000,
                    "version": system.get("comfyui_version", "unknown"),
                    "gpu": gpu_name,
                    "ram_free_gb": round(system.get("ram_free", 0) / 1e9, 1),
                    "python_version": system.get("python_version", "unknown")
                }
        except Exception:
            return 200, {"connected": False, "port": 8000, "error": "ComfyUI not reachable"}

    router.register_get("/api/presets", handle_get_presets)
    router.register_post("/api/preset", handle_create_preset)
    router.register_get("/api/comfyui/status", handle_comfyui_status)
```

- [ ] **Step 2: Verify syntax**

Run: `.venv/Scripts/python.exe -c "import api.endpoints.config; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add api/endpoints/config.py
git commit -m "feat: add config API endpoints (presets, comfyui status)"
```

---

### Task 7: Endpoint Handlers — Mask, Enhance, Split (`api/endpoints/mask.py`, `enhance.py`, `split.py`)

Granular pipeline control endpoints.

**Files:**
- Create: `api/endpoints/mask.py`
- Create: `api/endpoints/enhance.py`
- Create: `api/endpoints/split.py`

- [ ] **Step 1: Implement mask endpoints**

```python
# api/endpoints/mask.py
"""Mask endpoints: POST /api/mask/generate, POST /api/mask/refine"""
import os
import threading

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_generate(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        method = params.get("method", "comfyui")
        model = params.get("model", "BiRefNet-general")
        output_dir = params.get("output_dir", "output")

        job_id = router.jobs.create("mask", {"image": image, "method": method, "model": model})
        thread = threading.Thread(
            target=_run_mask_job,
            args=(router, job_id, image, method, model, output_dir),
            daemon=True
        )
        thread.start()
        return 202, {"job_id": job_id, "status": "queued"}

    def handle_refine(params):
        mask_path = params.get("mask")
        image_path = params.get("image")
        if not mask_path or not image_path:
            return 400, {"error": "Missing required fields: mask, image", "code": "BAD_REQUEST"}

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
        try:
            router.pool.reset_page(page)
            abs_image = os.path.join(PROJECT_DIR, image_path) if not os.path.isabs(image_path) else image_path
            router.bridge.load_image(page, abs_image)
            # Load the mask as AI mask
            abs_mask = os.path.join(PROJECT_DIR, mask_path) if not os.path.isabs(mask_path) else mask_path
            page.evaluate("() => document.querySelector('.card.closed')?.classList.remove('closed')")
            with page.expect_file_chooser() as fc:
                page.click('label[for="aiMaskInput"]')
            fc.value.set_files(abs_mask)
            page.wait_for_timeout(1000)
            # Apply refinement settings
            overrides = {}
            if "expand" in params: overrides["aiMaskExpand"] = params["expand"]
            if "feather" in params: overrides["aiMaskFeather"] = params["feather"]
            if "invert" in params: overrides["aiInvertMask"] = params["invert"]
            if overrides:
                router.bridge.apply_settings_override(page, overrides)
                page.wait_for_timeout(500)
            # Read coverage
            coverage = page.evaluate("""() => {
                const settings = getBgSettings();
                const refined = getRefinedImportedAiAlpha(settings);
                if (!refined) return 0;
                return getAlphaCoverage(refined);
            }""")
            # Save refined mask
            output_dir = params.get("output_dir", "output")
            abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
            os.makedirs(abs_output, exist_ok=True)
            base = os.path.splitext(os.path.basename(mask_path))[0]
            out_path = os.path.join(abs_output, f"{base}_refined.png")
            router.bridge.save_canvas_to_file(page, "aiMaskCanvas", out_path)
            return 200, {"refined_mask": out_path, "coverage": round(coverage, 4)}
        finally:
            router.pool.checkin(page)

    router.register_post("/api/mask/generate", handle_generate)
    router.register_post("/api/mask/refine", handle_refine)


def _run_mask_job(router, job_id, image, method, model, output_dir):
    router.jobs.update(job_id, status="processing", progress=0.1, step="Acquiring worker...")
    page = router.pool.checkout(timeout=30)
    if page is None:
        router.jobs.update(job_id, status="failed", error="Workers busy", code="POOL_EXHAUSTED")
        return
    try:
        router.pool.reset_page(page)
        abs_image = os.path.join(PROJECT_DIR, image) if not os.path.isabs(image) else image
        router.bridge.load_image(page, abs_image)
        router.jobs.update(job_id, progress=0.3, step="Generating mask...")
        # Set model
        page.evaluate(f"() => {{ const m = document.querySelector('#comfyuiModel'); if (m) m.value = '{model}'; }}")
        result = router.bridge.generate_mask_only(page)
        if not result.get("ok"):
            router.jobs.update(job_id, status="failed", error=result.get("error", "Mask generation failed"), code="MASK_FAILED")
            return
        abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
        os.makedirs(abs_output, exist_ok=True)
        base = os.path.splitext(os.path.basename(image))[0]
        mask_path = os.path.join(abs_output, f"{base}_mask.png")
        saved = router.bridge.save_canvas_to_file(page, "aiMaskCanvas", mask_path)
        router.jobs.update(job_id, status="completed", progress=1.0, results={
            "mask": mask_path, "coverage": result.get("coverage", 0),
            "auto_inverted": result.get("auto_inverted", False)
        })
    except Exception as e:
        router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
    finally:
        router.pool.checkin(page)
```

- [ ] **Step 2: Implement enhance endpoint**

```python
# api/endpoints/enhance.py
"""Enhance endpoint: POST /api/enhance"""
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_enhance(params):
        extracted = params.get("extracted")
        original = params.get("original")
        if not extracted or not original:
            return 400, {"error": "Missing required fields: extracted, original", "code": "BAD_REQUEST"}

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
        try:
            router.pool.reset_page(page)
            abs_original = os.path.join(PROJECT_DIR, original) if not os.path.isabs(original) else original
            abs_extracted = os.path.join(PROJECT_DIR, extracted) if not os.path.isabs(extracted) else extracted
            # Load original image
            router.bridge.load_image(page, abs_original)
            # Load extracted as the AI final canvas
            import base64
            with open(abs_extracted, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            page.evaluate(f"""(dataUrl) => {{
                return new Promise((resolve, reject) => {{
                    const img = new Image();
                    img.onload = () => {{
                        const c = document.querySelector('#aiFinalCanvas');
                        if (c) {{
                            c.width = img.width; c.height = img.height;
                            c.getContext('2d').drawImage(img, 0, 0);
                        }}
                        resolve(true);
                    }};
                    img.onerror = () => reject('load fail');
                    img.src = dataUrl;
                }});
            }}""", f"data:image/png;base64,{data}")
            page.wait_for_timeout(500)
            # Show AI enhance block and run
            page.evaluate("() => { const b = document.querySelector('#aiEnhanceBlock'); if (b) b.style.display = 'block'; }")
            result = router.bridge.run_enhance(page)
            if not result.get("ok"):
                return 500, {"error": "AI Enhance failed", "code": "ENHANCE_FAILED"}
            output_dir = params.get("output_dir", "output")
            abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
            os.makedirs(abs_output, exist_ok=True)
            base = os.path.splitext(os.path.basename(extracted))[0]
            out_path = os.path.join(abs_output, f"{base}_enhanced.png")
            router.bridge.save_canvas_to_file(page, "aiEnhancedCanvas", out_path)
            return 200, {"enhanced": out_path}
        finally:
            router.pool.checkin(page)

    router.register_post("/api/enhance", handle_enhance)
```

- [ ] **Step 3: Implement split endpoint**

```python
# api/endpoints/split.py
"""Split endpoint: POST /api/split"""
import os
import base64

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_split(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        min_pixels = params.get("min_pixels", 5000)
        alpha_cutoff = params.get("alpha_cutoff", 220)

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
        try:
            router.pool.reset_page(page)
            abs_image = os.path.join(PROJECT_DIR, image) if not os.path.isabs(image) else image
            # Load the image as source and as processed result
            router.bridge.load_image(page, abs_image)
            # Set split settings
            router.bridge.apply_settings_override(page, {
                "componentPixels": min_pixels,
                "componentAlpha": alpha_cutoff
            })
            # Run process to generate panels
            router.bridge.run_process_image(page, timeout_s=30)
            # Extract panels
            output_dir = params.get("output_dir", "output")
            abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
            os.makedirs(abs_output, exist_ok=True)
            base = os.path.splitext(os.path.basename(image))[0]
            panels = router.bridge.extract_panels(page, abs_output, base)
            return 200, {"panels": panels}
        finally:
            router.pool.checkin(page)

    router.register_post("/api/split", handle_split)
```

- [ ] **Step 4: Verify syntax for all three**

Run: `.venv/Scripts/python.exe -c "import api.endpoints.mask, api.endpoints.enhance, api.endpoints.split; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add api/endpoints/mask.py api/endpoints/enhance.py api/endpoints/split.py
git commit -m "feat: add mask, enhance, and split API endpoints"
```

---

### Task 8: Endpoint Handlers — Workflow (`api/endpoints/workflow.py`)

ComfyUI workflow builder endpoints.

**Files:**
- Create: `api/endpoints/workflow.py`

- [ ] **Step 1: Implement workflow endpoints**

```python
# api/endpoints/workflow.py
"""Workflow endpoints: POST /api/workflow/build, GET /api/workflow/templates"""
import json
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_build(params):
        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
        try:
            router.pool.reset_page(page)
            # Switch to Workflow Builder tab
            page.evaluate("() => { const tabs = document.querySelectorAll('.tab-btn'); if (tabs[1]) tabs[1].click(); }")
            page.wait_for_timeout(500)
            result = router.bridge.build_workflow(page, params)
            if "error" in result:
                return 500, {"error": result["error"], "code": "WORKFLOW_BUILD_FAILED"}

            # Also get install list and steps from DOM
            install_list = page.evaluate("""() => {
                const items = document.querySelectorAll('#installList li');
                return Array.from(items).map(li => li.textContent.trim());
            }""")
            steps = page.evaluate("""() => {
                const items = document.querySelectorAll('#stepsList li');
                return Array.from(items).map(li => li.textContent.trim());
            }""")
            result["install_list"] = install_list
            result["steps"] = steps
            return 200, result
        finally:
            router.pool.checkin(page)

    def handle_templates(params):
        templates = []
        for f in os.listdir(PROJECT_DIR):
            if f.startswith("starter-workflow-") and f.endswith(".json"):
                name = f.replace("starter-workflow-", "").replace(".json", "")
                templates.append({"name": name, "file": f})
        return 200, {"templates": templates}

    router.register_post("/api/workflow/build", handle_build)
    router.register_get("/api/workflow/templates", handle_templates)
```

- [ ] **Step 2: Verify syntax**

Run: `.venv/Scripts/python.exe -c "import api.endpoints.workflow; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add api/endpoints/workflow.py
git commit -m "feat: add workflow builder API endpoints"
```

---

### Task 9: Wire Everything into serve.py

Integrate the API layer into the existing server. Minimal changes to serve.py.

**Files:**
- Modify: `serve.py`

- [ ] **Step 1: Add API initialization and dispatch to serve.py**

Add imports and pool initialization at the top of `serve.py`, after existing imports:

```python
# After line 16 (import urllib.error), add:
import json as _json
import threading

# API layer
from api.jobs import JobManager
from api.pool import PlaywrightPool
from api.bridge import AppBridge
from api.router import APIRouter
from api.endpoints import extract as ep_extract
from api.endpoints import config as ep_config
from api.endpoints import mask as ep_mask
from api.endpoints import enhance as ep_enhance
from api.endpoints import split as ep_split
from api.endpoints import workflow as ep_workflow

# Global API components (initialized in __main__)
api_router = None
api_pool = None
```

Add API dispatch to `Handler.do_GET`:

```python
# Replace the existing do_GET (line 93-97) with:
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._handle_api("GET")
        elif self.path.startswith("/comfyui/"):
            self._proxy("GET")
        else:
            super().do_GET()
```

Add API dispatch to `Handler.do_POST`:

```python
# Replace the existing do_POST (line 99-105) with:
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

Add the `_handle_api` method to the Handler class:

```python
# Add after do_POST method:
    def _handle_api(self, method):
        body = None
        if method == "POST":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode() if content_length > 0 else ""
        status, response = api_router.handle_request(self, method, self.path, body)
        api_router.send_json(self, status, response)
```

Update the `__main__` block to initialize the API pool:

```python
# Replace __main__ block (lines 203-211) with:
if __name__ == "__main__":
    ensure_comfyui_running()

    # Initialize API layer
    job_manager = JobManager()
    api_pool = PlaywrightPool(f"http://127.0.0.1:{PORT}", size=2)
    bridge = AppBridge()
    api_router = APIRouter(job_manager, api_pool, bridge)

    # Register all endpoints
    ep_extract.register(api_router)
    ep_config.register(api_router)
    ep_mask.register(api_router)
    ep_enhance.register(api_router)
    ep_split.register(api_router)
    ep_workflow.register(api_router)

    with http.server.HTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        print(f"API at http://127.0.0.1:{PORT}/api/*")
        print(f"ComfyUI proxy at http://127.0.0.1:{PORT}/comfyui/*")
        print(f"ComfyUI backend: {COMFYUI_BASE}")
        print(f"Directory: {DIRECTORY}")

        # Start pool after server is listening (in background thread)
        def _start_pool():
            import time; time.sleep(2)
            print("Starting Playwright pool (2 workers)...")
            api_pool.start()
            print("Playwright pool ready.")
        pool_thread = threading.Thread(target=_start_pool, daemon=True)
        pool_thread.start()

        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        finally:
            if api_pool:
                api_pool.stop()
```

- [ ] **Step 2: Verify syntax**

Run: `.venv/Scripts/python.exe -c "import py_compile; py_compile.compile('serve.py', doraise=True); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add serve.py
git commit -m "feat: wire API automation layer into serve.py"
```

---

### Task 10: End-to-End API Tests

Test the full API through HTTP requests.

**Files:**
- Modify: `tests/test_api.py` (add e2e tests)

- [ ] **Step 1: Add e2e API tests**

Add to `tests/test_api.py`:

```python
import urllib.request
import json
import time

API_BASE = "http://127.0.0.1:8080/api"

def _api_get(path):
    req = urllib.request.Request(f"{API_BASE}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read())

def _api_post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{API_BASE}{path}", data=body,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read())

def _wait_for_job(job_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        status_code, job = _api_get(f"/status/{job_id}")
        if job["status"] in ("completed", "failed"):
            return job
        time.sleep(2)
    return {"status": "timeout"}

def test_e2e_presets():
    code, data = _api_get("/presets")
    assert code == 200
    assert "dark-balanced" in data["presets"]
    assert "light-balanced" in data["presets"]
    assert data["default"] == "dark-balanced"

def test_e2e_comfyui_status():
    code, data = _api_get("/comfyui/status")
    assert code == 200
    assert "connected" in data

def test_e2e_workflow_templates():
    code, data = _api_get("/workflow/templates")
    assert code == 200
    assert len(data["templates"]) >= 1

def test_e2e_extract():
    code, data = _api_post("/extract", {
        "image": "input/UI2.1.png",
        "preset": "light-balanced",
        "mode": "heuristic"
    })
    assert code == 202
    assert "job_id" in data
    job = _wait_for_job(data["job_id"], timeout=60)
    assert job["status"] == "completed", f"Job failed: {job}"
    assert "results" in job
    results = job["results"]
    assert results.get("sheet") or results.get("final")

def test_e2e_extract_ai_remove():
    code, data = _api_post("/extract", {
        "image": "input/UI2.1.png",
        "preset": "light-balanced",
        "mode": "ai-remove"
    })
    assert code == 202
    job = _wait_for_job(data["job_id"], timeout=120)
    assert job["status"] == "completed", f"Job failed: {job}"
    assert "alpha_stats" in job.get("results", {})

# In if __name__ block, add at the end:
    print("\n--- E2E API Tests ---")
    try:
        _api_get("/presets")  # quick connectivity check
        test_e2e_presets(); print("  PASS: e2e_presets")
        test_e2e_comfyui_status(); print("  PASS: e2e_comfyui_status")
        test_e2e_workflow_templates(); print("  PASS: e2e_workflow_templates")
        test_e2e_extract(); print("  PASS: e2e_extract")
        test_e2e_extract_ai_remove(); print("  PASS: e2e_extract_ai_remove")
    except urllib.error.URLError:
        print("  SKIP: e2e tests (API not running — restart serve.py with API layer)")
    except Exception as e:
        print(f"  E2E ERROR: {e}")
        import traceback; traceback.print_exc()
```

- [ ] **Step 2: Run all tests**

Run: `.venv/Scripts/python.exe tests/test_api.py`
Expected: Unit tests pass. E2E tests pass if serve.py is running with the API layer.

- [ ] **Step 3: Commit**

```bash
git add tests/test_api.py
git commit -m "feat: add end-to-end API tests"
```

---

## Task Dependency Order

```
Task 1 (jobs.py)           — no dependencies
Task 2 (pool.py)           — no dependencies
Task 3 (bridge.py)         — no dependencies
Task 4 (router.py)         — no dependencies
Task 5 (extract.py)        — depends on 1, 2, 3, 4
Task 6 (config.py)         — depends on 3, 4
Task 7 (mask/enhance/split)— depends on 1, 2, 3, 4
Task 8 (workflow.py)       — depends on 3, 4
Task 9 (serve.py wiring)   — depends on ALL above
Task 10 (e2e tests)        — depends on 9
```

**Parallelizable:** Tasks 1-4 can all be built simultaneously. Tasks 5-8 can be built simultaneously after 1-4. Task 9 wires everything. Task 10 validates.
