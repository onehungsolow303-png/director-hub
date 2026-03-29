"""Canvas extraction and wait helpers for Playwright browser automation.

Extracts HTML5 canvas elements as PIL Images via toDataURL().
Provides polling-based wait functions for async processing completion.
"""

import base64
import time
from io import BytesIO
from pathlib import Path

from PIL import Image


def extract_canvas(page, selector: str) -> Image.Image | None:
    """Extract a canvas element as a PIL RGBA Image via toDataURL."""
    data_url = page.evaluate(f"""() => {{
        const c = document.querySelector('{selector}');
        if (!c || c.width <= 1 || c.height <= 1) return null;
        return c.toDataURL('image/png');
    }}""")
    if not data_url:
        return None
    return _decode_data_url(data_url)


def extract_canvas_js(page, js_expression: str) -> Image.Image | None:
    """Extract a canvas via a custom JS expression that returns a data URL."""
    data_url = page.evaluate(js_expression)
    if not data_url:
        return None
    return _decode_data_url(data_url)


def extract_processed_layout(page) -> Image.Image | None:
    """Extract the processedLayoutCanvas JS global variable."""
    return extract_canvas_js(page, """() => {
        if (typeof processedLayoutCanvas === 'undefined' || !processedLayoutCanvas) return null;
        if (processedLayoutCanvas.width <= 1) return null;
        return processedLayoutCanvas.toDataURL('image/png');
    }""")


def save_canvas_to_file(page, selector: str, out_path: str | Path) -> Image.Image | None:
    """Extract canvas and save to disk. Returns PIL Image or None."""
    img = extract_canvas(page, selector)
    if img:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
    return img


def wait_for_status(page, selector: str, target_text: str,
                    timeout: float = 60, poll_interval: float = 1.0,
                    fail_texts: tuple = ("failed", "error")) -> str:
    """Poll a DOM element's textContent until it contains target_text."""
    start = time.time()
    while time.time() - start < timeout:
        text = page.evaluate(f"""() => {{
            const el = document.querySelector('{selector}');
            return el ? el.textContent : '';
        }}""")
        if target_text.lower() in text.lower():
            return text
        for fail in fail_texts:
            if fail.lower() in text.lower():
                return f"FAIL: {text}"
        time.sleep(poll_interval)
    return "TIMEOUT"


def wait_ai_remove(page, timeout: float = 90) -> str:
    """Wait for AI Remove to complete. Returns status string."""
    start = time.time()
    while time.time() - start < timeout:
        status = page.evaluate("""() => {
            const el = document.querySelector('#aiRemoveStatus');
            return el ? el.textContent : '';
        }""")
        if "Done" in status or "Review" in status:
            return status
        if "failed" in status.lower() or "error" in status.lower():
            return f"FAIL: {status}"
        btn_dis = page.evaluate(
            "() => document.querySelector('#aiRemoveButton')?.disabled"
        )
        if not btn_dis and time.time() - start > 5:
            sz = page.evaluate(
                "() => { const c = document.querySelector('#resultCanvas'); return c ? c.width : 0; }"
            )
            if sz > 1:
                return status or "completed"
        time.sleep(2)
    return "TIMEOUT"


def wait_process_image(page, timeout: float = 30) -> str:
    """Wait for heuristic Process Image to complete."""
    return wait_for_status(page, "#bgStatus", "Done.", timeout=timeout,
                           poll_interval=0.5)


def wait_enhance(page, timeout: float = 15) -> str:
    """Wait for AI Enhance to complete."""
    return wait_for_status(page, "#aiEnhanceStatus", "complete",
                           timeout=timeout, poll_interval=1.0)


def _decode_data_url(data_url: str) -> Image.Image | None:
    """Decode a base64 data URL to a PIL Image."""
    header = "data:image/png;base64,"
    if not data_url.startswith(header):
        return None
    raw = base64.b64decode(data_url[len(header):])
    return Image.open(BytesIO(raw)).convert("RGBA")
