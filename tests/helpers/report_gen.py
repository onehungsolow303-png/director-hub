"""HTML visual diff report generator.

Produces a self-contained HTML report with:
- Side-by-side reference vs result images (base64 embedded)
- Diff heatmap visualization
- Quality metrics table per test case
- Pass/fail summary
"""

import base64
import json
from io import BytesIO
from pathlib import Path

from jinja2 import Template
from PIL import Image

from helpers.quality_metrics import generate_diff_heatmap

REPORT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Quality Test Report</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
  h1 { color: #64ffda; margin-bottom: 20px; }
  h2 { color: #bb86fc; margin: 20px 0 10px; }
  .summary { display: flex; gap: 20px; margin-bottom: 30px; }
  .stat-box { background: #16213e; padding: 16px 24px; border-radius: 8px; text-align: center; }
  .stat-box .value { font-size: 28px; font-weight: bold; }
  .stat-box .label { font-size: 12px; color: #888; margin-top: 4px; }
  .pass { color: #64ffda; }
  .fail { color: #ff5252; }
  .warn { color: #ffd740; }
  .test-case { background: #16213e; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
  .test-case h3 { margin-bottom: 12px; }
  .images { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
  .images figure { text-align: center; }
  .images img { max-width: 400px; max-height: 300px; border: 1px solid #333;
                background: repeating-conic-gradient(#333 0% 25%, #222 0% 50%) 50%/16px 16px; }
  .images figcaption { font-size: 11px; color: #888; margin-top: 4px; }
  table { border-collapse: collapse; margin: 10px 0; width: 100%; }
  th, td { padding: 6px 12px; text-align: left; border-bottom: 1px solid #333; }
  th { color: #bb86fc; font-size: 12px; }
  td { font-size: 13px; }
  .gate-pass { color: #64ffda; }
  .gate-fail { color: #ff5252; }
</style>
</head>
<body>
<h1>Quality Test Report</h1>

<div class="summary">
  <div class="stat-box">
    <div class="value">{{ total }}</div>
    <div class="label">TOTAL TESTS</div>
  </div>
  <div class="stat-box">
    <div class="value pass">{{ passed }}</div>
    <div class="label">PASSED</div>
  </div>
  <div class="stat-box">
    <div class="value fail">{{ failed }}</div>
    <div class="label">FAILED</div>
  </div>
</div>

{% for case in cases %}
<div class="test-case">
  <h3>
    <span class="{{ 'pass' if case.passed else 'fail' }}">
      {{ '&#10004;' if case.passed else '&#10008;' }}
    </span>
    {{ case.name }}
  </h3>

  <div class="images">
    <figure>
      <img src="data:image/png;base64,{{ case.ref_b64 }}" alt="Reference">
      <figcaption>Reference</figcaption>
    </figure>
    <figure>
      <img src="data:image/png;base64,{{ case.result_b64 }}" alt="Result">
      <figcaption>Result</figcaption>
    </figure>
    {% if case.diff_b64 %}
    <figure>
      <img src="data:image/png;base64,{{ case.diff_b64 }}" alt="Diff Heatmap">
      <figcaption>Diff Heatmap</figcaption>
    </figure>
    {% endif %}
  </div>

  <table>
    <tr><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>
    {% for m in case.metrics_table %}
    <tr>
      <td>{{ m.name }}</td>
      <td>{{ m.value }}</td>
      <td>{{ m.threshold }}</td>
      <td class="{{ 'gate-pass' if m.passed else 'gate-fail' }}">
        {{ 'PASS' if m.passed else 'FAIL' }}
      </td>
    </tr>
    {% endfor %}
  </table>

  {% if case.alpha_stats %}
  <h4 style="margin-top:10px; color:#64ffda;">Alpha Stats</h4>
  <table>
    <tr><th></th><th>Transparent%</th><th>Semi%</th><th>Opaque%</th></tr>
    <tr><td>Reference</td>
        <td>{{ case.alpha_stats.ref.transparent }}</td>
        <td>{{ case.alpha_stats.ref.semi }}</td>
        <td>{{ case.alpha_stats.ref.opaque }}</td></tr>
    <tr><td>Result</td>
        <td>{{ case.alpha_stats.test.transparent }}</td>
        <td>{{ case.alpha_stats.test.semi }}</td>
        <td>{{ case.alpha_stats.test.opaque }}</td></tr>
  </table>
  {% endif %}
</div>
{% endfor %}

</body>
</html>"""


def _img_to_b64(img: Image.Image, max_size: tuple = (800, 600)) -> str:
    """Convert PIL Image to base64 PNG string, resized for report embedding."""
    thumb = img.copy()
    thumb.thumbnail(max_size, Image.LANCZOS)
    buf = BytesIO()
    thumb.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def build_report_case(name: str, ref_img: Image.Image, result_img: Image.Image,
                      gate_result: dict) -> dict:
    """Build a single test case entry for the HTML report."""
    metrics = gate_result.get("metrics", {})

    metrics_table = []
    gate_checks = [
        ("pHash Distance", "phash_distance", "phash_max_distance", lambda v, t: v <= t),
        ("PSNR (dB)", "psnr_db", "psnr_min_db", lambda v, t: v >= t),
        ("SSIM", "ssim", "ssim_min", lambda v, t: v >= t),
        ("Alpha IoU", "alpha_iou", "alpha_iou_min", lambda v, t: v >= t),
        ("Alpha MAE", "alpha_mae", "alpha_mae_max", lambda v, t: v <= t),
    ]

    from helpers.quality_metrics import DEFAULT_THRESHOLDS
    for display_name, metric_key, threshold_key, check_fn in gate_checks:
        value = metrics.get(metric_key, "N/A")
        threshold = DEFAULT_THRESHOLDS.get(threshold_key, "N/A")
        passed = check_fn(value, threshold) if isinstance(value, (int, float)) else False
        metrics_table.append({
            "name": display_name,
            "value": f"{value}" if value != "N/A" else "N/A",
            "threshold": f"{threshold}",
            "passed": passed,
        })

    diff_img = generate_diff_heatmap(result_img, ref_img)

    alpha_stats_data = None
    if "alpha_stats" in metrics and "ref_alpha_stats" in metrics:
        alpha_stats_data = {
            "test": metrics["alpha_stats"],
            "ref": metrics["ref_alpha_stats"],
        }

    return {
        "name": name,
        "passed": gate_result.get("passed", False),
        "ref_b64": _img_to_b64(ref_img),
        "result_b64": _img_to_b64(result_img),
        "diff_b64": _img_to_b64(diff_img),
        "metrics_table": metrics_table,
        "alpha_stats": alpha_stats_data,
    }


def generate_html_report(cases: list[dict], output_path: str | Path):
    """Render the full HTML report and save to disk."""
    total = len(cases)
    passed = sum(1 for c in cases if c["passed"])
    failed = total - passed

    template = Template(REPORT_TEMPLATE)
    html = template.render(total=total, passed=passed, failed=failed, cases=cases)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def save_json_report(cases: list[dict], gate_results: dict, output_path: str | Path):
    """Save machine-readable JSON metrics report."""
    report = {}
    for name in cases:
        gr = gate_results.get(name, {})
        report[name] = {
            "passed": gr.get("passed", False),
            "failed_at": gr.get("failed_at"),
            "metrics": {k: v for k, v in gr.get("metrics", {}).items()
                        if not isinstance(v, dict)},
        }
        if "alpha_stats" in gr.get("metrics", {}):
            report[name]["alpha_stats"] = gr["metrics"]["alpha_stats"]
        if "ref_alpha_stats" in gr.get("metrics", {}):
            report[name]["ref_alpha_stats"] = gr["metrics"]["ref_alpha_stats"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
