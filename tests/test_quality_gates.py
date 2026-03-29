"""Quality gate tests — compare extracted results against golden reference images.

Runs progressive quality gates (pHash -> PSNR -> SSIM -> Alpha IoU -> Alpha MAE)
on extraction outputs. Produces HTML visual diff report and JSON metrics.

Run: .venv/Scripts/python.exe -m pytest tests/test_quality_gates.py -v -m quality
"""

import json
import math
from pathlib import Path

import pytest
from PIL import Image

from helpers.quality_metrics import (
    run_quality_gates,
    alpha_stats,
    region_opaque_pct,
    DEFAULT_THRESHOLDS,
)
from helpers.report_gen import build_report_case, generate_html_report, save_json_report

ROOT = Path(r"C:\Dev\Image generator")
REPORTS_DIR = ROOT / "tests" / "reports"
DIFFS_DIR = REPORTS_DIR / "diffs"


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that converts numpy scalar types to native Python types."""

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


_report_cases = []
_gate_results = {}


def _load_extraction_result(test_name: str) -> "Image.Image | None":
    """Load the extraction result from a prior live test run.

    The conftest output_dir fixture converts test node names like
    ``test_dark_extraction[dark-balanced]`` to
    ``test_dark_extraction_dark_balanced`` (brackets removed, dashes to
    underscores, no trailing separator).
    """
    test_dir = DIFFS_DIR / test_name
    for fname in ["ai_final.png", "result.png", "result_canvas.png", "processed_layout.png"]:
        path = test_dir / fname
        if path.exists():
            return Image.open(path).convert("RGBA")
    return None


@pytest.mark.quality
@pytest.mark.parametrize("preset", ["dark-balanced", "dark-soft", "dark-hard"])
def test_dark_quality(preset, golden_images, output_dir):
    """Compare dark preset extraction against dark reference with progressive quality gates."""
    # conftest output_dir converts "[dark-balanced]" -> "_dark_balanced" (no trailing underscore)
    test_key = f"test_dark_extraction_{preset.replace('-', '_')}"
    result_img = _load_extraction_result(test_key)
    if result_img is None:
        pytest.skip(f"No extraction output found for {preset}. Run live tests first.")

    ref_img = golden_images.get("dark_ref_full")
    assert ref_img is not None, "Dark reference image not found in golden/"

    gate_result = run_quality_gates(result_img, ref_img)
    _gate_results[f"dark-{preset}"] = gate_result

    case = build_report_case(f"dark / {preset}", ref_img, result_img, gate_result)
    _report_cases.append(case)

    topbar = region_opaque_pct(result_img, 0, 1, 0, 0.10)
    botbar = region_opaque_pct(result_img, 0, 1, 0.70, 1.0)
    portrait = region_opaque_pct(result_img, 0, 0.10, 0.60, 1.0)

    metrics_path = output_dir / "quality_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "preset": preset,
            "passed": gate_result["passed"],
            "failed_at": gate_result["failed_at"],
            "metrics": {k: v for k, v in gate_result["metrics"].items()
                        if not isinstance(v, dict)},
            "regions": {"topbar": topbar, "botbar": botbar, "portrait": portrait},
            "alpha_stats": gate_result["metrics"].get("alpha_stats"),
        }, f, indent=2, cls=_NumpyEncoder)

    if not gate_result["passed"]:
        failures_str = "; ".join(
            f"{name}={val} (need {thresh})"
            for name, val, thresh in gate_result["failures"]
        )
        pytest.fail(f"Quality gates FAILED for {preset}: {failures_str}")


@pytest.mark.quality
@pytest.mark.parametrize("preset", ["light-balanced", "light-soft", "light-hard"])
def test_light_quality(preset, golden_images, output_dir):
    """Compare light preset extraction against light reference with progressive quality gates."""
    # conftest output_dir converts "[light-balanced]" -> "_light_balanced" (no trailing underscore)
    test_key = f"test_light_extraction_{preset.replace('-', '_')}"
    result_img = _load_extraction_result(test_key)
    if result_img is None:
        pytest.skip(f"No extraction output found for {preset}. Run live tests first.")

    ref_img = golden_images.get("light_ref_full")
    assert ref_img is not None, "Light reference image not found in golden/"

    gate_result = run_quality_gates(result_img, ref_img)
    _gate_results[f"light-{preset}"] = gate_result

    case = build_report_case(f"light / {preset}", ref_img, result_img, gate_result)
    _report_cases.append(case)

    metrics_path = output_dir / "quality_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "preset": preset,
            "passed": gate_result["passed"],
            "failed_at": gate_result["failed_at"],
            "metrics": {k: v for k, v in gate_result["metrics"].items()
                        if not isinstance(v, dict)},
            "alpha_stats": gate_result["metrics"].get("alpha_stats"),
        }, f, indent=2, cls=_NumpyEncoder)

    if not gate_result["passed"]:
        failures_str = "; ".join(
            f"{name}={val} (need {thresh})"
            for name, val, thresh in gate_result["failures"]
        )
        pytest.fail(f"Quality gates FAILED for {preset}: {failures_str}")


@pytest.fixture(scope="session", autouse=True)
def generate_reports(request):
    """Generate HTML and JSON reports after all quality tests complete."""
    yield

    if _report_cases:
        html_path = REPORTS_DIR / "quality_report.html"
        generate_html_report(_report_cases, html_path)
        print(f"\n  HTML report: {html_path}")

    if _gate_results:
        json_path = REPORTS_DIR / "quality_report.json"
        save_json_report(list(_gate_results.keys()), _gate_results, json_path)
        print(f"  JSON report: {json_path}")
