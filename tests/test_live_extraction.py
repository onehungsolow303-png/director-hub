"""Live browser extraction tests — full workflow through the real app.

Parameterized across all 6 presets × 2 source images.
Each test: upload image → select preset → run extraction → extract canvas → save output.

Run: .venv/Scripts/python.exe tests/launcher.py tests/test_live_extraction.py -v -m live
"""

import json
from pathlib import Path

import pytest
from PIL import Image

from helpers.app_driver import (
    load_app,
    upload_image,
    open_advanced_settings,
    select_preset,
    run_ai_remove,
    run_process_image,
)
from helpers.canvas_extract import (
    extract_canvas,
    extract_processed_layout,
    save_canvas_to_file,
)

ROOT = Path(r"C:\Dev\Image generator")
REPORTS_DIR = ROOT / "tests" / "reports"


@pytest.mark.live
@pytest.mark.slow
@pytest.mark.parametrize("preset", ["dark-balanced", "dark-soft", "dark-hard"])
def test_dark_extraction(page, dark_source_path, preset, output_dir):
    """Run dark preset extraction via AI Remove and verify output canvas is populated."""
    load_app(page)
    upload_image(page, dark_source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_ai_remove(page, timeout=90)
    assert "FAIL" not in status, f"AI Remove failed: {status}"
    assert "TIMEOUT" not in status, f"AI Remove timed out after 90s"

    page.screenshot(path=str(output_dir / "01_after_ai_remove.png"))

    result_img = extract_canvas(page, "#aiFinalCanvas")
    if result_img:
        result_img.save(str(output_dir / "ai_final.png"), "PNG")
    else:
        result_img = extract_canvas(page, "#resultCanvas")
        if result_img:
            result_img.save(str(output_dir / "result_canvas.png"), "PNG")

    assert result_img is not None, "No result canvas produced"
    assert result_img.width > 1 and result_img.height > 1, "Result canvas is too small"

    meta_path = output_dir / "extraction_meta.json"
    with open(meta_path, "w") as f:
        json.dump({
            "preset": preset,
            "tone": "dark",
            "mode": "ai-remove",
            "status": status,
            "result_size": [result_img.width, result_img.height],
        }, f, indent=2)

    page.screenshot(path=str(output_dir / "02_final.png"))


@pytest.mark.live
@pytest.mark.slow
@pytest.mark.parametrize("preset", ["light-balanced", "light-soft", "light-hard"])
def test_light_extraction(page, light_source_path, preset, output_dir):
    """Run light preset extraction via Process Image and verify output canvas is populated."""
    load_app(page)
    upload_image(page, light_source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_process_image(page, timeout=30)
    assert "FAIL" not in status, f"Process Image failed: {status}"
    assert "TIMEOUT" not in status, f"Process Image timed out after 30s"

    page.screenshot(path=str(output_dir / "01_after_process.png"))

    layout_img = extract_processed_layout(page)
    result_img = layout_img or extract_canvas(page, "#resultCanvas")

    if result_img:
        result_img.save(str(output_dir / "result.png"), "PNG")

    assert result_img is not None, "No result canvas produced"
    assert result_img.width > 1 and result_img.height > 1, "Result canvas is too small"

    meta_path = output_dir / "extraction_meta.json"
    with open(meta_path, "w") as f:
        json.dump({
            "preset": preset,
            "tone": "light",
            "mode": "heuristic",
            "status": status,
            "result_size": [result_img.width, result_img.height],
        }, f, indent=2)

    page.screenshot(path=str(output_dir / "02_final.png"))
