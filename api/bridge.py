"""
AppBridge — translation layer between API requests and app.js page.evaluate() calls.

Each method receives a Playwright `page` object (from PlaywrightPool) and drives
the browser app headlessly, returning plain Python dicts/values.
"""

import base64
import os
import time
from typing import Any, Callable, Dict, List, Optional

# Project root is two levels up from this file (api/ → project root)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppBridge:
    """Playwright-to-app.js bridge for API automation."""

    # ------------------------------------------------------------------
    # Image loading
    # ------------------------------------------------------------------

    def load_image(self, page, image_path: str) -> Dict[str, Any]:
        """Trigger the file chooser, load an image, return {loaded, width, height}."""
        abs_path = os.path.abspath(image_path)

        with page.expect_file_chooser() as fc_info:
            page.click("#bgInputFile")
        file_chooser = fc_info.value
        file_chooser.set_files(abs_path)

        # Wait for the image to be drawn onto the original canvas
        page.wait_for_function(
            "() => { const c = document.querySelector('#originalCanvas'); return c && c.width > 0; }",
            timeout=15000,
        )

        result = page.evaluate(
            """() => {
                const c = document.querySelector('#originalCanvas');
                return { loaded: c && c.width > 0, width: c ? c.width : 0, height: c ? c.height : 0 };
            }"""
        )
        return result

    def load_image_base64(self, page, data_url: str) -> Dict[str, Any]:
        """Load a base64 data URL directly into app globals via an Image element."""
        result = page.evaluate(
            """(dataUrl) => {
                return new Promise((resolve, reject) => {
                    const img = new Image();
                    img.onload = () => {
                        // Mirror what the app does when a file is loaded
                        window.loadedImage = img;
                        const originalCanvas = document.querySelector('#originalCanvas');
                        if (originalCanvas) {
                            originalCanvas.width = img.width;
                            originalCanvas.height = img.height;
                            originalCanvas.getContext('2d').drawImage(img, 0, 0);
                        }
                        resolve({ loaded: true, width: img.width, height: img.height });
                    };
                    img.onerror = (e) => reject(new Error('Failed to load image from data URL'));
                    img.src = dataUrl;
                });
            }""",
            data_url,
        )
        return result

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def apply_preset(self, page, preset_name: str) -> Dict[str, Any]:
        """Open the Advanced Settings card (if closed) and select a preset."""
        # Ensure the Advanced Settings card is open
        page.evaluate(
            """() => {
                const cards = document.querySelectorAll('.card');
                for (const card of cards) {
                    const header = card.querySelector('.card-header h3');
                    if (header && header.textContent.trim() === 'Advanced Settings') {
                        if (card.classList.contains('closed')) {
                            card.classList.remove('closed');
                        }
                        break;
                    }
                }
            }"""
        )

        # Set the preset select value and fire the change event so applyPreset() runs
        result = page.evaluate(
            """(presetName) => {
                const sel = document.querySelector('#bgPreset');
                if (!sel) return { ok: false, error: 'bgPreset element not found' };
                const options = Array.from(sel.options).map(o => o.value);
                if (!options.includes(presetName)) {
                    return { ok: false, error: 'Preset not found: ' + presetName, available: options };
                }
                sel.value = presetName;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
                return { ok: true, preset: presetName };
            }""",
            preset_name,
        )
        return result

    def apply_settings_override(self, page, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Set individual form controls by their element id.

        For <input type="range">, <input type="number">, <select>: sets .value.
        For <input type="checkbox">: sets .checked.
        Dispatches an 'input' event after each change so reactive handlers fire.
        """
        result = page.evaluate(
            """(overrides) => {
                const applied = {};
                const failed = {};
                for (const [id, value] of Object.entries(overrides)) {
                    const el = document.getElementById(id);
                    if (!el) { failed[id] = 'element not found'; continue; }
                    if (el.type === 'checkbox') {
                        el.checked = Boolean(value);
                    } else {
                        el.value = String(value);
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    applied[id] = value;
                }
                return { applied, failed };
            }""",
            overrides,
        )
        return result

    def get_current_settings(self, page) -> Dict[str, Any]:
        """Call getBgSettings() in app.js and return the result."""
        return page.evaluate("() => getBgSettings()")

    # ------------------------------------------------------------------
    # Processing operations (with polling)
    # ------------------------------------------------------------------

    def run_ai_remove(
        self,
        page,
        on_progress: Optional[Callable[[str], None]] = None,
        timeout_s: int = 300,
    ) -> Dict[str, Any]:
        """Click AI Remove button and poll #aiRemoveStatus until done or timeout."""
        page.click("#aiRemoveButton")

        deadline = time.time() + timeout_s
        last_text = ""
        while time.time() < deadline:
            time.sleep(1)
            status = page.evaluate(
                "() => { const el = document.querySelector('#aiRemoveStatus'); return el ? el.textContent : ''; }"
            )
            if status != last_text:
                last_text = status
                if on_progress:
                    on_progress(status)
            # Terminal states
            if status and ("Done." in status or "done" in status.lower()):
                return {"ok": True, "status": status}
            if status and ("failed" in status.lower() or "error" in status.lower()):
                return {"ok": False, "status": status, "error": status}
            # Also check isProcessing flag
            still_processing = page.evaluate("() => typeof isProcessing !== 'undefined' ? isProcessing : true")
            if not still_processing and last_text:
                return {"ok": True, "status": last_text}

        return {"ok": False, "status": last_text, "error": "timeout"}

    def run_process_image(
        self,
        page,
        on_progress: Optional[Callable[[str], None]] = None,
        timeout_s: int = 120,
    ) -> Dict[str, Any]:
        """Click Process Image button and poll #bgStatus until done or timeout."""
        page.click("#processBgButton")

        deadline = time.time() + timeout_s
        last_text = ""
        while time.time() < deadline:
            time.sleep(1)
            status = page.evaluate(
                "() => { const el = document.querySelector('#bgStatus'); return el ? el.textContent : ''; }"
            )
            if status != last_text:
                last_text = status
                if on_progress:
                    on_progress(status)
            still_processing = page.evaluate("() => typeof isProcessing !== 'undefined' ? isProcessing : false")
            if not still_processing:
                return {"ok": True, "status": last_text}

        return {"ok": False, "status": last_text, "error": "timeout"}

    def run_enhance(self, page) -> Dict[str, Any]:
        """Click AI Enhance and wait for the enhanced canvas to be populated."""
        page.click("#aiEnhanceButton")

        # Wait for aiEnhancedCanvas to have non-trivial dimensions
        try:
            page.wait_for_function(
                "() => { const c = document.querySelector('#aiEnhancedCanvas'); return c && c.width > 1; }",
                timeout=60000,
            )
            dims = page.evaluate(
                """() => {
                    const c = document.querySelector('#aiEnhancedCanvas');
                    return { width: c.width, height: c.height };
                }"""
            )
            return {"ok": True, **dims}
        except Exception as exc:
            status = page.evaluate(
                "() => { const el = document.querySelector('#aiEnhanceStatus'); return el ? el.textContent : ''; }"
            )
            return {"ok": False, "error": str(exc), "status": status}

    # ------------------------------------------------------------------
    # Canvas extraction
    # ------------------------------------------------------------------

    def extract_alpha_stats(self, page, canvas_id: str) -> Dict[str, Any]:
        """Read alpha channel of a canvas and return % transparent / semi / opaque pixels."""
        return page.evaluate(
            """(canvasId) => {
                const canvas = document.getElementById(canvasId)
                    || document.querySelector('#' + canvasId);
                if (!canvas || canvas.width === 0) {
                    return { ok: false, error: 'canvas not found or empty', canvasId };
                }
                const ctx = canvas.getContext('2d');
                const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                const total = canvas.width * canvas.height;
                let transparent = 0, semi = 0, opaque = 0;
                for (let i = 3; i < data.length; i += 4) {
                    const a = data[i];
                    if (a === 0) transparent++;
                    else if (a === 255) opaque++;
                    else semi++;
                }
                return {
                    ok: true,
                    canvasId,
                    width: canvas.width,
                    height: canvas.height,
                    total,
                    transparent,
                    semi,
                    opaque,
                    pct_transparent: Math.round(transparent / total * 10000) / 100,
                    pct_semi: Math.round(semi / total * 10000) / 100,
                    pct_opaque: Math.round(opaque / total * 10000) / 100,
                };
            }""",
            canvas_id,
        )

    def save_canvas_to_file(self, page, canvas_id: str, output_path: str) -> Dict[str, Any]:
        """Extract a canvas as PNG via toDataURL and save it to output_path."""
        data_url = page.evaluate(
            """(canvasId) => {
                const canvas = document.getElementById(canvasId)
                    || document.querySelector('#' + canvasId);
                if (!canvas || canvas.width === 0) return null;
                return canvas.toDataURL('image/png');
            }""",
            canvas_id,
        )
        if not data_url:
            return {"ok": False, "error": f"Canvas '{canvas_id}' not found or empty"}

        # data_url is "data:image/png;base64,<b64>"
        header, b64_data = data_url.split(",", 1)
        png_bytes = base64.b64decode(b64_data)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as fh:
            fh.write(png_bytes)

        return {"ok": True, "path": output_path, "bytes": len(png_bytes)}

    # ------------------------------------------------------------------
    # Bulk extraction helpers
    # ------------------------------------------------------------------

    def extract_all_results(
        self, page, output_dir: str, base_name: str
    ) -> Dict[str, Any]:
        """Save all result canvases (result, aiFinal, aiEnhanced, originalCanvas),
        plus split panels, plus a mask canvas, plus alpha stats for each."""
        os.makedirs(output_dir, exist_ok=True)
        saved = {}
        stats = {}

        canvas_targets = {
            "result": "resultCanvas",
            "original": "originalCanvas",
            "ai_final": "aiFinalCanvas",
            "ai_enhanced": "aiEnhancedCanvas",
        }

        for label, cid in canvas_targets.items():
            out_path = os.path.join(output_dir, f"{base_name}_{label}.png")
            r = self.save_canvas_to_file(page, cid, out_path)
            saved[label] = r
            if r.get("ok"):
                stats[label] = self.extract_alpha_stats(page, cid)

        # Save panels
        panels_result = self.extract_panels(page, output_dir, base_name)
        saved["panels"] = panels_result

        # Mask — try processedMaskCanvas or manualMaskCanvas via JS
        mask_path = os.path.join(output_dir, f"{base_name}_mask.png")
        mask_data_url = page.evaluate(
            """() => {
                const src = window.processedMaskCanvas || window.manualMaskCanvas || window.aiMaskCanvas;
                if (!src || src.width === 0) return null;
                return src.toDataURL('image/png');
            }"""
        )
        if mask_data_url:
            header, b64_data = mask_data_url.split(",", 1)
            png_bytes = base64.b64decode(b64_data)
            with open(mask_path, "wb") as fh:
                fh.write(png_bytes)
            saved["mask"] = {"ok": True, "path": mask_path, "bytes": len(png_bytes)}
        else:
            saved["mask"] = {"ok": False, "error": "no mask canvas available"}

        return {"saved": saved, "alpha_stats": stats}

    def extract_panels(
        self, page, output_dir: str, base_name: str
    ) -> Dict[str, Any]:
        """Save each panel from processedPanels JS array as individual PNG files."""
        os.makedirs(output_dir, exist_ok=True)

        panel_data_urls = page.evaluate(
            """() => {
                if (!window.processedPanels || !window.processedPanels.length) return [];
                return window.processedPanels.map((panel, idx) => {
                    const canvas = (panel.canvas && panel.canvas.width > 0)
                        ? panel.canvas : (panel.fullCanvas || null);
                    if (!canvas) return null;
                    return canvas.toDataURL('image/png');
                }).filter(Boolean);
            }"""
        )

        saved_panels = []
        for i, data_url in enumerate(panel_data_urls):
            header, b64_data = data_url.split(",", 1)
            png_bytes = base64.b64decode(b64_data)
            out_path = os.path.join(output_dir, f"{base_name}_panel_{i:03d}.png")
            with open(out_path, "wb") as fh:
                fh.write(png_bytes)
            saved_panels.append({"index": i, "path": out_path, "bytes": len(png_bytes)})

        return {"ok": True, "count": len(saved_panels), "panels": saved_panels}

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def get_presets(self, page) -> Dict[str, Any]:
        """Read bgPresets from app.js and return as a Python dict."""
        return page.evaluate("() => typeof bgPresets !== 'undefined' ? bgPresets : {}")

