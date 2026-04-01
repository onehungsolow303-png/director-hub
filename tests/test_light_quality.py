"""
Light background extraction quality test.
Compares heuristic presets (light-balanced, light-soft, light-hard)
and AI Remove against reference quality examples.

Usage:
    .venv/Scripts/python.exe tests/test_light_quality.py
"""

import os
import sys
import time
import json
from pathlib import Path
from PIL import Image
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT / "input" / "Example quality image extraction" / "Light background examples"
REPORT_DIR = PROJECT / "test_screenshots" / "light_quality_report"
APP_URL = "http://127.0.0.1:8080"

SOURCE_IMAGE = INPUT_DIR / "Original Image White background.png"
REFERENCE_FILES = {
    "full_sheet": INPUT_DIR / "example preview ectraction white background removed.PNG",
    "top_bar":    INPUT_DIR / "example extracted final asset top bar white background removed.PNG",
    "bottom_bar": INPUT_DIR / "example extracted final asset bottom bar dark background.PNG",
    "portrait":   INPUT_DIR / "example extracted final asset bottom left box asset. white background removed.PNG",
}

HEURISTIC_PRESETS = ["light-balanced", "light-soft", "light-hard"]
TIMEOUT_MS = 30_000

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Alpha analysis helpers
# ---------------------------------------------------------------------------
def alpha_stats(img: Image.Image) -> dict:
    """Return alpha channel statistics for a PIL Image."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    total = alpha.size
    transparent = int(np.sum(alpha == 0))
    opaque = int(np.sum(alpha == 255))
    semi = total - transparent - opaque
    return {
        "width": img.width,
        "height": img.height,
        "total_px": total,
        "transparent": transparent,
        "opaque": opaque,
        "semi": semi,
        "pct_transparent": round(100 * transparent / total, 2),
        "pct_opaque": round(100 * opaque / total, 2),
        "pct_semi": round(100 * semi / total, 2),
        "alpha_mean": round(float(np.mean(alpha)), 2),
    }


def canvas_alpha_stats_js():
    """JS snippet that reads the result canvas and returns alpha stats."""
    return """() => {
        const rc = document.querySelector('#resultCanvas');
        if (!rc || rc.width === 0) return null;
        const ctx = rc.getContext('2d');
        const d = ctx.getImageData(0, 0, rc.width, rc.height).data;
        let transparent = 0, opaque = 0, semi = 0;
        for (let i = 3; i < d.length; i += 4) {
            if (d[i] === 0) transparent++;
            else if (d[i] === 255) opaque++;
            else semi++;
        }
        const total = rc.width * rc.height;
        return {
            width: rc.width, height: rc.height, total_px: total,
            transparent, opaque, semi,
            pct_transparent: +(100 * transparent / total).toFixed(2),
            pct_opaque: +(100 * opaque / total).toFixed(2),
            pct_semi: +(100 * semi / total).toFixed(2),
        };
    }"""


def count_split_panels_js():
    """JS snippet that counts split gallery cards."""
    return "() => document.querySelectorAll('.split-card').length"


def get_split_panel_dims_js():
    """JS snippet that returns dimensions of each split panel canvas."""
    return """() => {
        const cards = document.querySelectorAll('.split-card canvas');
        return Array.from(cards).map(c => ({w: c.width, h: c.height}));
    }"""


# ---------------------------------------------------------------------------
# Playwright test helpers
# ---------------------------------------------------------------------------
def load_image_into_app(page):
    """Upload the source image via the file input."""
    file_input = page.locator("#bgInputFile")
    file_input.set_input_files(str(SOURCE_IMAGE))
    # Wait for the image to render on the source canvas
    page.wait_for_function(
        "() => { const c = document.querySelector('#originalCanvas'); return c && c.width > 100; }",
        timeout=10_000,
    )
    time.sleep(0.5)


def open_advanced_settings(page):
    """Open any collapsed .card sections."""
    page.evaluate('() => document.querySelectorAll(".card.closed").forEach(c => c.classList.remove("closed"))')
    time.sleep(0.3)


def set_preset(page, preset_name):
    """Select a preset from the dropdown."""
    page.select_option("#bgPreset", preset_name)
    time.sleep(0.3)


def click_process_and_wait(page, timeout_s=30):
    """Click Process Image and poll bgStatus for 'Done.' or error."""
    page.click("#processBgButton")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status_text = page.text_content("#bgStatus") or ""
        if "Done." in status_text:
            return status_text
        if "failed" in status_text.lower() or "error" in status_text.lower():
            return status_text
        time.sleep(0.5)
    return f"TIMEOUT after {timeout_s}s — last status: {page.text_content('#bgStatus')}"


def click_ai_remove_and_wait(page, timeout_s=60):
    """Click AI Remove and poll aiRemoveStatus for completion."""
    page.click("#aiRemoveButton")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        ai_status = page.text_content("#aiRemoveStatus") or ""
        bg_status = page.text_content("#bgStatus") or ""
        if "Done." in ai_status:
            return ai_status
        if "failed" in ai_status.lower() or "error" in ai_status.lower():
            return f"AI_FAIL: {ai_status}"
        if "failed" in bg_status.lower():
            return f"BG_FAIL: {bg_status}"
        time.sleep(1)
    return f"TIMEOUT after {timeout_s}s — ai: {page.text_content('#aiRemoveStatus')} bg: {page.text_content('#bgStatus')}"


def save_screenshot(page, name):
    """Save a full-page screenshot."""
    path = REPORT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def save_result_canvas(page, name):
    """Save the result canvas as a PNG and return alpha stats."""
    path = REPORT_DIR / f"{name}_result.png"
    # Export canvas to data URL then save
    data_url = page.evaluate("""() => {
        const rc = document.querySelector('#resultCanvas');
        if (!rc || rc.width === 0) return null;
        return rc.toDataURL('image/png');
    }""")
    if data_url:
        import base64
        header, encoded = data_url.split(",", 1)
        with open(path, "wb") as f:
            f.write(base64.b64decode(encoded))
        stats = page.evaluate(canvas_alpha_stats_js())
        return path, stats
    return None, None


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------
def run_tests():
    from playwright.sync_api import sync_playwright

    results = {}

    # -- Reference image analysis --
    print("=" * 70)
    print("REFERENCE IMAGE ANALYSIS")
    print("=" * 70)
    ref_stats = {}
    for label, fpath in REFERENCE_FILES.items():
        if fpath.exists():
            img = Image.open(fpath)
            stats = alpha_stats(img)
            ref_stats[label] = stats
            print(f"  {label}: {stats['width']}x{stats['height']}  "
                  f"transparent={stats['pct_transparent']}%  "
                  f"opaque={stats['pct_opaque']}%  "
                  f"semi={stats['pct_semi']}%")
        else:
            print(f"  {label}: FILE NOT FOUND at {fpath}")
            ref_stats[label] = None
    results["reference"] = ref_stats

    # -- Playwright tests --
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # --- Heuristic presets ---
        for preset in HEURISTIC_PRESETS:
            tag = preset.replace("-", "_")
            print(f"\n{'=' * 70}")
            print(f"TESTING PRESET: {preset}")
            print(f"{'=' * 70}")

            context = browser.new_context(viewport={"width": 1400, "height": 1000})
            page = context.new_page()
            page.goto(APP_URL, wait_until="networkidle")
            time.sleep(1)

            # Load image
            load_image_into_app(page)
            print(f"  Image loaded.")

            # Open advanced, set preset
            open_advanced_settings(page)
            set_preset(page, preset)
            print(f"  Preset '{preset}' selected.")

            # Take settings screenshot
            save_screenshot(page, f"{tag}_settings")

            # Process
            status_text = click_process_and_wait(page, timeout_s=30)
            print(f"  Status: {status_text[:120]}")

            # Save result
            canvas_path, canvas_stats = save_result_canvas(page, tag)
            save_screenshot(page, f"{tag}_page")

            # Count panels
            panel_count = page.evaluate(count_split_panels_js())
            panel_dims = page.evaluate(get_split_panel_dims_js())
            print(f"  Panels found: {panel_count}")
            if canvas_stats:
                print(f"  Canvas: {canvas_stats['width']}x{canvas_stats['height']}  "
                      f"transparent={canvas_stats['pct_transparent']}%  "
                      f"opaque={canvas_stats['pct_opaque']}%  "
                      f"semi={canvas_stats['pct_semi']}%")
            else:
                print(f"  Canvas: NO RESULT")

            results[preset] = {
                "status": status_text[:200],
                "canvas_stats": canvas_stats,
                "panel_count": panel_count,
                "panel_dims": panel_dims,
            }

            context.close()

        # --- AI Remove (light-balanced) ---
        print(f"\n{'=' * 70}")
        print(f"TESTING: AI Remove (light-balanced)")
        print(f"{'=' * 70}")

        context = browser.new_context(viewport={"width": 1400, "height": 1000})
        page = context.new_page()
        page.goto(APP_URL, wait_until="networkidle")
        time.sleep(1)

        load_image_into_app(page)
        open_advanced_settings(page)

        # Set tone to light, preset to light-balanced
        page.select_option("#bgTone", "light")
        time.sleep(0.3)
        set_preset(page, "light-balanced")

        save_screenshot(page, "light_ai_settings")

        status_text = click_ai_remove_and_wait(page, timeout_s=60)
        print(f"  Status: {status_text[:120]}")

        canvas_path, canvas_stats = save_result_canvas(page, "light_ai")
        save_screenshot(page, "light_ai_page")
        panel_count = page.evaluate(count_split_panels_js())
        panel_dims = page.evaluate(get_split_panel_dims_js())

        if canvas_stats:
            print(f"  Canvas: {canvas_stats['width']}x{canvas_stats['height']}  "
                  f"transparent={canvas_stats['pct_transparent']}%  "
                  f"opaque={canvas_stats['pct_opaque']}%  "
                  f"semi={canvas_stats['pct_semi']}%")
        else:
            print(f"  Canvas: NO RESULT")
        print(f"  Panels found: {panel_count}")

        ai_failed = "TIMEOUT" in status_text or "FAIL" in status_text or "failed" in status_text.lower()
        results["light-ai"] = {
            "status": status_text[:200],
            "canvas_stats": canvas_stats,
            "panel_count": panel_count,
            "panel_dims": panel_dims,
            "ai_failed": ai_failed,
        }

        context.close()
        browser.close()

    # ---------------------------------------------------------------------------
    # Quality comparison table
    # ---------------------------------------------------------------------------
    print(f"\n\n{'=' * 110}")
    print("QUALITY COMPARISON TABLE")
    print(f"{'=' * 110}")

    # Reference full-sheet stats (primary comparison target)
    ref_full = ref_stats.get("full_sheet")
    ref_top = ref_stats.get("top_bar")
    ref_bottom = ref_stats.get("bottom_bar")
    ref_portrait = ref_stats.get("portrait")

    # Determine if reference panels have expected characteristics
    ref_transparent_pct = ref_full["pct_transparent"] if ref_full else "N/A"
    ref_panels = sum(1 for v in [ref_top, ref_bottom, ref_portrait] if v is not None)

    columns = ["Reference", "light-balanced", "light-soft", "light-hard", "light-ai"]
    col_data = {}

    # Reference column
    col_data["Reference"] = {
        "transparent_pct": ref_transparent_pct,
        "opaque_pct": ref_full["pct_opaque"] if ref_full else "N/A",
        "semi_pct": ref_full["pct_semi"] if ref_full else "N/A",
        "panels_found": f"{ref_panels} (ref assets)",
        "top_bar": "Y" if ref_top else "N",
        "bottom_bar": "Y" if ref_bottom else "N",
        "portrait": "Y" if ref_portrait else "N",
        "dimensions": f"{ref_full['width']}x{ref_full['height']}" if ref_full else "N/A",
    }

    # Test columns
    for key in ["light-balanced", "light-soft", "light-hard", "light-ai"]:
        r = results.get(key, {})
        cs = r.get("canvas_stats")
        pc = r.get("panel_count", 0)
        dims = r.get("panel_dims", [])
        failed = r.get("ai_failed", False) if key == "light-ai" else ("Done." not in r.get("status", ""))

        if cs and not failed:
            # Heuristic check for top bar / bottom bar presence based on panel dimensions
            # A top bar is typically wide and short, a bottom bar similarly
            has_wide_panel = any(d.get("w", 0) > 200 and d.get("h", 0) < d.get("w", 0) for d in dims) if dims else False
            has_tall_panel = any(d.get("h", 0) > d.get("w", 0) * 0.8 for d in dims) if dims else False

            col_data[key] = {
                "transparent_pct": cs["pct_transparent"],
                "opaque_pct": cs["pct_opaque"],
                "semi_pct": cs["pct_semi"],
                "panels_found": pc,
                "top_bar": "Y" if has_wide_panel or pc >= 2 else "?",
                "bottom_bar": "Y" if pc >= 2 else "?",
                "portrait": "Y" if pc >= 3 else "?",
                "dimensions": f"{cs['width']}x{cs['height']}",
            }
        else:
            status_short = "AI unavail." if key == "light-ai" and failed else "FAIL"
            col_data[key] = {
                "transparent_pct": status_short,
                "opaque_pct": status_short,
                "semi_pct": status_short,
                "panels_found": status_short,
                "top_bar": status_short,
                "bottom_bar": status_short,
                "portrait": status_short,
                "dimensions": status_short,
            }

    # Print table
    metrics = [
        ("Dimensions",     "dimensions"),
        ("Transparent %",  "transparent_pct"),
        ("Opaque %",       "opaque_pct"),
        ("Semi-trans %",   "semi_pct"),
        ("Panels found",   "panels_found"),
        ("Top bar",        "top_bar"),
        ("Bottom bar",     "bottom_bar"),
        ("Portrait frame", "portrait"),
    ]

    header = f"{'Metric':<18}"
    for col in columns:
        header += f" | {col:>16}"
    print(header)
    print("-" * len(header))

    for metric_label, metric_key in metrics:
        row = f"{metric_label:<18}"
        for col in columns:
            val = col_data.get(col, {}).get(metric_key, "N/A")
            if isinstance(val, float):
                val = f"{val:.1f}%"
            row += f" | {str(val):>16}"
        print(row)

    print(f"\n{'=' * 110}")

    # ---------------------------------------------------------------------------
    # Detailed quality comparison against reference
    # ---------------------------------------------------------------------------
    if ref_full:
        ref_t = ref_full["pct_transparent"]
        print(f"\nQUALITY NOTES vs REFERENCE (full sheet transparent = {ref_t:.1f}%):")
        for key in ["light-balanced", "light-soft", "light-hard", "light-ai"]:
            r = results.get(key, {})
            cs = r.get("canvas_stats")
            if cs:
                delta = cs["pct_transparent"] - ref_t
                direction = "more" if delta > 0 else "less"
                quality = "CLOSE" if abs(delta) < 5 else ("AGGRESSIVE" if delta > 0 else "CONSERVATIVE")
                print(f"  {key:>18}: transparent={cs['pct_transparent']:.1f}%  "
                      f"delta={delta:+.1f}% ({direction}) — {quality}")
            else:
                print(f"  {key:>18}: NO RESULT")

    # Save JSON report
    report_path = REPORT_DIR / "quality_report.json"
    # Convert non-serializable values
    serializable = {}
    for k, v in results.items():
        if isinstance(v, dict):
            serializable[k] = {}
            for k2, v2 in v.items():
                if isinstance(v2, dict) and k == "reference":
                    serializable[k][k2] = v2
                else:
                    serializable[k][k2] = v2
        else:
            serializable[k] = v

    with open(report_path, "w") as f:
        json.dump(serializable, f, indent=2, default=str)
    print(f"\nFull report saved to: {report_path}")
    print(f"Screenshots saved to: {REPORT_DIR}")


if __name__ == "__main__":
    run_tests()
