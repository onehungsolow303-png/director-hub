"""App driver for browser automation — upload, configure, process, extract.

High-level functions that combine Playwright page interactions
with canvas extraction and wait helpers into complete workflows.
"""

from pathlib import Path

from PIL import Image

from helpers.canvas_extract import (
    extract_canvas,
    extract_processed_layout,
    save_canvas_to_file,
    wait_ai_remove,
    wait_process_image,
    wait_enhance,
)

APP_URL = "http://127.0.0.1:8080"


def load_app(page, url: str = APP_URL):
    """Navigate to the app and wait for it to be ready."""
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(2000)


def upload_image(page, image_path: str | Path):
    """Upload a source image via the file input."""
    page.set_input_files("#bgInputFile", str(image_path))
    page.wait_for_timeout(3000)


def open_advanced_settings(page):
    """Expand all collapsed card sections."""
    page.evaluate(
        '() => document.querySelectorAll(".card.closed")'
        '.forEach(c => c.classList.remove("closed"))'
    )
    page.wait_for_timeout(500)


def select_preset(page, preset: str):
    """Select an extraction preset from the dropdown."""
    page.select_option("#bgPreset", preset)
    page.wait_for_timeout(500)


def select_tone(page, tone: str):
    """Select background tone ('dark' or 'light')."""
    page.select_option("#bgTone", tone)
    page.wait_for_timeout(300)


def run_ai_remove(page, timeout: float = 90) -> str:
    """Click AI Remove and wait for completion. Returns status string."""
    page.click("#aiRemoveButton")
    return wait_ai_remove(page, timeout=timeout)


def run_process_image(page, timeout: float = 30) -> str:
    """Click Process Image (heuristic) and wait for completion."""
    page.click("#processBgButton")
    return wait_process_image(page, timeout=timeout)


def run_enhance(page, timeout: float = 15) -> str:
    """Click AI Enhance if available. Returns status or 'NOT_VISIBLE'."""
    page.evaluate(
        "() => { const b = document.querySelector('#aiEnhanceButton');"
        " if(b) b.scrollIntoView(); }"
    )
    page.wait_for_timeout(500)
    visible = page.evaluate(
        "() => { const b = document.querySelector('#aiEnhanceBlock');"
        " return b ? b.style.display !== 'none' : false; }"
    )
    if not visible:
        return "NOT_VISIBLE"
    page.click("#aiEnhanceButton")
    page.wait_for_timeout(5000)
    return wait_enhance(page, timeout=timeout)


def extract_best_result(page) -> Image.Image | None:
    """Extract the best available result canvas.
    Priority: aiEnhancedCanvas > aiFinalCanvas > processedLayoutCanvas > resultCanvas
    """
    for selector in ["#aiEnhancedCanvas", "#aiFinalCanvas"]:
        img = extract_canvas(page, selector)
        if img:
            return img
    layout = extract_processed_layout(page)
    if layout:
        return layout
    return extract_canvas(page, "#resultCanvas")


def run_dark_extraction(page, source_path: str | Path, preset: str,
                        out_dir: Path | None = None) -> dict:
    """Full dark-preset extraction workflow: load → configure → AI Remove → extract."""
    load_app(page)
    upload_image(page, source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_ai_remove(page, timeout=90)
    result = {"status": status, "result_img": None, "enhanced_img": None, "screenshots": []}

    if "FAIL" in status or "TIMEOUT" in status:
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_dir / "failed.png"))
        return result

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_dir / "01_after_ai_remove.png"))
        result["result_img"] = save_canvas_to_file(page, "#aiFinalCanvas",
                                                    out_dir / "ai_final.png")
    else:
        result["result_img"] = extract_canvas(page, "#aiFinalCanvas")

    enh_status = run_enhance(page)
    if enh_status not in ("NOT_VISIBLE", "TIMEOUT"):
        if out_dir:
            result["enhanced_img"] = save_canvas_to_file(page, "#aiEnhancedCanvas",
                                                          out_dir / "ai_enhanced.png")
            page.screenshot(path=str(out_dir / "02_final.png"))
        else:
            result["enhanced_img"] = extract_canvas(page, "#aiEnhancedCanvas")

    return result


def run_light_extraction(page, source_path: str | Path, preset: str,
                         out_dir: Path | None = None) -> dict:
    """Full light-preset extraction workflow: load → configure → Process Image → extract."""
    load_app(page)
    upload_image(page, source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_process_image(page, timeout=30)
    result = {"status": status, "result_img": None, "enhanced_img": None, "screenshots": []}

    if "FAIL" in status or "TIMEOUT" in status:
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_dir / "failed.png"))
        return result

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_dir / "01_after_process.png"))
        result["result_img"] = save_canvas_to_file(page, "#resultCanvas",
                                                    out_dir / "result_canvas.png")
        layout = extract_processed_layout(page)
        if layout:
            layout.save(str(out_dir / "processed_layout.png"), "PNG")
            result["result_img"] = layout
    else:
        result["result_img"] = extract_processed_layout(page) or extract_canvas(page, "#resultCanvas")

    return result
