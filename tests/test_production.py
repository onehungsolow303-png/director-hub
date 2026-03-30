"""Production quality test — compare Enhanced (Color Restored) output against
user-verified reference extraction examples.

Uploads real source images through the browser, runs AI Remove + Enhance,
extracts #aiEnhancedCanvas, and compares against reference using quality metrics.

Run: .venv/Scripts/python.exe tests/launcher.py tests/test_production.py -v
"""

import json
import math
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
    run_enhance,
)
from helpers.canvas_extract import extract_processed_layout
from helpers.canvas_extract import extract_canvas, save_canvas_to_file
from helpers.quality_metrics import (
    alpha_iou,
    alpha_mae,
    alpha_stats,
    compute_ssim,
    compute_psnr,
    compute_phash_distance,
    generate_diff_heatmap,
)

ROOT = Path(r"C:\Dev\Image generator")
REPORTS_DIR = ROOT / "tests" / "reports"

# Progressive quality tiers
TIERS = {
    1: {"alpha_iou_min": 0.90, "ssim_min": 0.30, "alpha_mae_max": 12.0},
    2: {"alpha_iou_min": 0.93, "ssim_min": 0.40, "alpha_mae_max": 8.0},
    3: {"alpha_iou_min": 0.95, "ssim_min": 0.50, "alpha_mae_max": 5.0},
}


class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        except ImportError:
            pass
        return super().default(obj)


def _run_and_extract(page, source_path, preset, out_dir):
    """Upload image, run AI Remove + Enhance, extract Enhanced canvas."""
    load_app(page)
    upload_image(page, source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_ai_remove(page, timeout=90)
    if "FAIL" in status or "TIMEOUT" in status:
        page.screenshot(path=str(out_dir / "failed.png"))
        return None, status

    page.screenshot(path=str(out_dir / "01_after_ai_remove.png"))
    save_canvas_to_file(page, "#aiFinalCanvas", out_dir / "ai_final.png")

    enh_status = run_enhance(page, timeout=15)
    enhanced_img = None
    if enh_status not in ("NOT_VISIBLE", "TIMEOUT"):
        enhanced_img = save_canvas_to_file(page, "#aiEnhancedCanvas",
                                            out_dir / "ai_enhanced.png")
        page.screenshot(path=str(out_dir / "02_after_enhance.png"))

    if enhanced_img is None:
        enhanced_img = extract_canvas(page, "#aiFinalCanvas")
        if enhanced_img:
            enhanced_img.save(str(out_dir / "ai_enhanced_fallback.png"), "PNG")

    return enhanced_img, status


def _run_and_extract_light(page, source_path, preset, out_dir):
    """Upload image, run Process Image (light mode), extract result canvas."""
    load_app(page)
    upload_image(page, source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_process_image(page, timeout=30)
    if "FAIL" in status or "TIMEOUT" in status:
        page.screenshot(path=str(out_dir / "failed.png"))
        return None, status

    page.screenshot(path=str(out_dir / "01_after_process.png"))

    # Try processedLayoutCanvas first, then resultCanvas
    result_img = extract_processed_layout(page)
    if result_img:
        result_img.save(str(out_dir / "processed_layout.png"), "PNG")
    else:
        result_img = extract_canvas(page, "#resultCanvas")
        if result_img:
            result_img.save(str(out_dir / "result_canvas.png"), "PNG")

    return result_img, status


def _compare_and_report(test_img, ref_img, out_dir, test_name):
    """Compare extraction against reference, save metrics and diff."""
    iou = alpha_iou(test_img, ref_img)
    mae = alpha_mae(test_img, ref_img)
    ssim = compute_ssim(test_img, ref_img)
    psnr = compute_psnr(test_img, ref_img)
    phash = compute_phash_distance(test_img, ref_img)
    t_stats = alpha_stats(test_img)
    r_stats = alpha_stats(ref_img)

    diff = generate_diff_heatmap(test_img, ref_img)
    diff.save(str(out_dir / "diff_heatmap.png"), "PNG")

    metrics = {
        "alpha_iou": iou,
        "alpha_mae": mae,
        "ssim": ssim,
        "psnr_db": psnr,
        "phash_distance": phash,
        "alpha_stats": t_stats,
        "ref_alpha_stats": r_stats,
    }

    with open(out_dir / "production_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, cls=_NumpyEncoder)

    return metrics


_prod_results = {}


@pytest.mark.production
def test_production_dark(page, prod_dark_source, prod_dark_ref, prod_tier, output_dir):
    """Production test: dark background extraction vs user reference."""
    out_dir = REPORTS_DIR / "diffs" / "test_production_dark"
    out_dir.mkdir(parents=True, exist_ok=True)

    enhanced_img, status = _run_and_extract(page, prod_dark_source,
                                             "dark-balanced", out_dir)
    assert enhanced_img is not None, f"Extraction failed: {status}"

    metrics = _compare_and_report(enhanced_img, prod_dark_ref, out_dir,
                                   "production_dark")
    _prod_results["dark"] = metrics

    tier = TIERS.get(prod_tier, TIERS[1])
    failures = []
    if metrics["alpha_iou"] < tier["alpha_iou_min"]:
        failures.append(f"alpha_iou={metrics['alpha_iou']:.4f} (need >= {tier['alpha_iou_min']})")
    if metrics["ssim"] < tier["ssim_min"]:
        failures.append(f"ssim={metrics['ssim']:.4f} (need >= {tier['ssim_min']})")
    if metrics["alpha_mae"] > tier["alpha_mae_max"]:
        failures.append(f"alpha_mae={metrics['alpha_mae']:.2f} (need <= {tier['alpha_mae_max']})")

    if failures:
        pytest.fail(f"Production dark FAILED (tier {prod_tier}): {'; '.join(failures)}")


@pytest.mark.production
def test_production_light(page, prod_light_source, prod_light_ref, prod_tier, output_dir):
    """Production test: light background extraction vs user reference."""
    out_dir = REPORTS_DIR / "diffs" / "test_production_light"
    out_dir.mkdir(parents=True, exist_ok=True)

    enhanced_img, status = _run_and_extract_light(page, prod_light_source,
                                                    "light-balanced", out_dir)
    assert enhanced_img is not None, f"Extraction failed: {status}"

    metrics = _compare_and_report(enhanced_img, prod_light_ref, out_dir,
                                   "production_light")
    _prod_results["light"] = metrics

    tier = TIERS.get(prod_tier, TIERS[1])
    failures = []
    if metrics["alpha_iou"] < tier["alpha_iou_min"]:
        failures.append(f"alpha_iou={metrics['alpha_iou']:.4f} (need >= {tier['alpha_iou_min']})")
    if metrics["ssim"] < tier["ssim_min"]:
        failures.append(f"ssim={metrics['ssim']:.4f} (need >= {tier['ssim_min']})")
    if metrics["alpha_mae"] > tier["alpha_mae_max"]:
        failures.append(f"alpha_mae={metrics['alpha_mae']:.2f} (need <= {tier['alpha_mae_max']})")

    if failures:
        pytest.fail(f"Production light FAILED (tier {prod_tier}): {'; '.join(failures)}")


@pytest.fixture(scope="session", autouse=True)
def save_production_report(request):
    """Save combined production report after all production tests complete."""
    yield
    if _prod_results:
        report_path = REPORTS_DIR / "production_report.json"
        with open(report_path, "w") as f:
            json.dump(_prod_results, f, indent=2, cls=_NumpyEncoder)
        print(f"\n  Production report: {report_path}")
