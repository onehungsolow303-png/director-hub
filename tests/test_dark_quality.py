"""
Dark background extraction quality test.

Compares the app's dark-balanced / dark-soft / dark-hard presets against
reference quality examples using Playwright + PIL.

Usage:
    .venv/Scripts/python.exe tests/test_dark_quality.py
"""

import os
import sys
import time
import json
import math
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────
ROOT = Path(r"C:\Dev\Image generator")
APP_URL = "http://127.0.0.1:8080"
REF_DIR = ROOT / "input" / "Example quality image extraction" / "Dark background examples"
OUT_DIR = ROOT / "test_screenshots" / "dark_quality_report"
SOURCE_IMAGE = REF_DIR / "Original Image dark background.png"

REFERENCE_FILES = {
    "full_sheet": REF_DIR / "example preview ectraction dark background removed.PNG",
    "top_bar": REF_DIR / "example extracted final asset top bar dark background removed.PNG",
    "bottom_bar": REF_DIR / "example extracted final asset bottom bar dark background.PNG",
    "portrait_frame": REF_DIR / "example extracted final asset bottom left box asset. dark background removed.PNG",
}

PRESETS = ["dark-balanced", "dark-soft", "dark-hard"]

# ── Helpers ───────────────────────────────────────────────────────────

def alpha_stats(img: Image.Image) -> dict:
    """Return % transparent, semi-transparent, opaque from RGBA image."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3].ravel()
    total = len(alpha)
    transparent = int(np.sum(alpha == 0))
    opaque = int(np.sum(alpha == 255))
    semi = total - transparent - opaque
    return {
        "transparent_pct": round(100.0 * transparent / total, 2),
        "semi_pct": round(100.0 * semi / total, 2),
        "opaque_pct": round(100.0 * opaque / total, 2),
        "total_pixels": total,
    }


def compare_images(ref: Image.Image, test: Image.Image) -> dict:
    """Compare two RGBA images, returning similarity metrics."""
    # Resize test to match ref if needed
    if ref.size != test.size:
        test_resized = test.resize(ref.size, Image.LANCZOS)
    else:
        test_resized = test
    ref_arr = np.array(ref.convert("RGBA")).astype(np.float64)
    test_arr = np.array(test_resized.convert("RGBA")).astype(np.float64)

    # Mean absolute error per channel
    mae = np.mean(np.abs(ref_arr - test_arr))
    # Alpha channel similarity
    alpha_mae = np.mean(np.abs(ref_arr[:, :, 3] - test_arr[:, :, 3]))
    # Structural: both transparent overlap
    ref_transparent = ref_arr[:, :, 3] < 10
    test_transparent = test_arr[:, :, 3] < 10
    ref_opaque = ref_arr[:, :, 3] > 245
    test_opaque = test_arr[:, :, 3] > 245

    # Intersection over union for transparent regions
    trans_intersection = np.sum(ref_transparent & test_transparent)
    trans_union = np.sum(ref_transparent | test_transparent)
    trans_iou = trans_intersection / max(1, trans_union)

    opaque_intersection = np.sum(ref_opaque & test_opaque)
    opaque_union = np.sum(ref_opaque | test_opaque)
    opaque_iou = opaque_intersection / max(1, opaque_union)

    return {
        "same_size": ref.size == test.size,
        "ref_size": ref.size,
        "test_size": test.size,
        "mae_all_channels": round(mae, 2),
        "mae_alpha": round(alpha_mae, 2),
        "transparent_iou": round(trans_iou, 4),
        "opaque_iou": round(opaque_iou, 4),
    }


def classify_panel(w, h, full_w, full_h):
    """Guess what UI element a panel might be based on aspect ratio + position hint."""
    aspect = w / max(1, h)
    w_ratio = w / max(1, full_w)
    h_ratio = h / max(1, full_h)
    if aspect >= 3.5 and h_ratio <= 0.2:
        return "bar"  # Could be top or bottom bar
    if w_ratio <= 0.35 and h_ratio <= 0.45 and 0.6 <= aspect <= 1.8:
        return "portrait_frame"
    return "other"


def save_canvas_as_png(page, canvas_selector, out_path):
    """Save a canvas element as a PNG file using toDataURL."""
    data_url = page.evaluate(f"""() => {{
        const c = document.querySelector('{canvas_selector}');
        if (!c || c.width <= 1 || c.height <= 1) return null;
        return c.toDataURL('image/png');
    }}""")
    if not data_url:
        return None
    import base64
    header = "data:image/png;base64,"
    if data_url.startswith(header):
        raw = base64.b64decode(data_url[len(header):])
        with open(out_path, "wb") as f:
            f.write(raw)
        return out_path
    return None


def get_canvas_size(page, selector):
    """Return (width, height) of a canvas element."""
    return page.evaluate(f"""() => {{
        const c = document.querySelector('{selector}');
        return c ? [c.width, c.height] : [0, 0];
    }}""")


def get_split_panel_info(page):
    """Extract info about split panels from the DOM."""
    return page.evaluate("""() => {
        const cards = document.querySelectorAll('#splitLinks .split-card');
        const result = [];
        cards.forEach((card) => {
            const strong = card.querySelector('strong');
            const badge = card.querySelector('.split-card-badge');
            const meta = card.querySelector('.split-card-meta');
            const canvas = card.querySelector('canvas');
            result.push({
                title: strong ? strong.textContent : '',
                label: badge ? badge.textContent : '',
                meta: meta ? meta.textContent : '',
                width: canvas ? canvas.width : 0,
                height: canvas ? canvas.height : 0,
                isLikelyUi: badge ? !badge.classList.contains('split-card-badge-warning') : false,
            });
        });
        return result;
    }""")


def save_split_panels(page, preset_dir):
    """Save each split panel canvas as a separate PNG."""
    panel_count = page.evaluate("""() => {
        return document.querySelectorAll('#splitLinks .split-card canvas').length;
    }""")
    saved = []
    for i in range(panel_count):
        data_url = page.evaluate(f"""(idx) => {{
            const canvases = document.querySelectorAll('#splitLinks .split-card canvas');
            if (idx >= canvases.length) return null;
            return canvases[idx].toDataURL('image/png');
        }}""", i)
        if data_url:
            import base64
            header = "data:image/png;base64,"
            if data_url.startswith(header):
                out_path = preset_dir / f"panel_{i+1:02d}.png"
                raw = base64.b64decode(data_url[len(header):])
                with open(out_path, "wb") as f:
                    f.write(raw)
                saved.append(out_path)
    return saved


def wait_for_ai_remove(page, timeout=180):
    """Wait for AI Remove to complete by monitoring status text."""
    start = time.time()
    while time.time() - start < timeout:
        status_text = page.evaluate("""() => {
            const el = document.querySelector('#aiRemoveStatus');
            return el ? el.textContent : '';
        }""")
        btn_disabled = page.evaluate("""() => {
            const btn = document.querySelector('#aiRemoveButton');
            return btn ? btn.disabled : false;
        }""")
        if "Done" in status_text or "failed" in status_text.lower():
            return status_text
        if "Review results" in status_text:
            return status_text
        # Also check if button re-enabled after being disabled
        if not btn_disabled and "Step" not in status_text and time.time() - start > 5:
            # Button re-enabled, check if we have a result
            canvas_size = get_canvas_size(page, "#resultCanvas")
            if canvas_size[0] > 1 and canvas_size[1] > 1:
                return status_text or "completed (button re-enabled)"
        time.sleep(2)
    return "TIMEOUT"


def wait_for_enhance(page, timeout=30):
    """Wait for AI Enhance to complete."""
    start = time.time()
    while time.time() - start < timeout:
        status_text = page.evaluate("""() => {
            const el = document.querySelector('#aiEnhanceStatus');
            return el ? el.textContent : '';
        }""")
        if "complete" in status_text.lower() or "compare" in status_text.lower():
            return status_text
        time.sleep(1)
    return "TIMEOUT"


def run_preset_test(browser, preset, out_dir):
    """Run a single preset test: load image, set preset, AI Remove, AI Enhance."""
    preset_dir = out_dir / preset
    preset_dir.mkdir(parents=True, exist_ok=True)

    context = browser.new_context()
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(APP_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)

    print(f"\n  [{preset}] Loading source image...")
    # Upload the source image via file input
    page.set_input_files("#bgInputFile", str(SOURCE_IMAGE))
    page.wait_for_timeout(3000)

    # Open advanced settings to access preset selector
    # The Advanced Settings card starts closed -- click its header to open
    page.evaluate("""() => {
        const cards = document.querySelectorAll('.card');
        for (const card of cards) {
            const h3 = card.querySelector('h3');
            if (h3 && h3.textContent.includes('Advanced')) {
                card.classList.remove('closed');
            }
        }
    }""")
    page.wait_for_timeout(500)

    # Set preset
    print(f"  [{preset}] Setting preset...")
    page.select_option("#bgPreset", preset)
    page.wait_for_timeout(500)

    # Take a pre-process screenshot
    page.screenshot(path=str(preset_dir / "00_loaded.png"))

    # Click AI Remove
    print(f"  [{preset}] Running AI Remove...")
    page.click("#aiRemoveButton")
    status = wait_for_ai_remove(page, timeout=180)
    print(f"  [{preset}] AI Remove status: {status}")
    page.screenshot(path=str(preset_dir / "01_after_ai_remove.png"))

    if "failed" in status.lower() or "TIMEOUT" in status:
        print(f"  [{preset}] FAILED: {status}")
        context.close()
        return None

    # Save aiFinalCanvas (which gets populated after AI Remove via showAiEnhanceBlock)
    save_canvas_as_png(page, "#aiFinalCanvas", preset_dir / "ai_final.png")

    # Save resultCanvas
    save_canvas_as_png(page, "#resultCanvas", preset_dir / "result_canvas.png")

    # Get panel info
    panels = get_split_panel_info(page)
    print(f"  [{preset}] Panels detected: {len(panels)}")
    for p in panels:
        print(f"    {p['title']}: {p['meta']} - {p['label']} (UI={p['isLikelyUi']})")

    # Save individual panels
    panel_files = save_split_panels(page, preset_dir)
    print(f"  [{preset}] Saved {len(panel_files)} panel images")

    # Click AI Enhance
    print(f"  [{preset}] Running AI Enhance...")
    # Scroll to make the enhance button visible
    page.evaluate("""() => {
        const btn = document.querySelector('#aiEnhanceButton');
        if (btn) btn.scrollIntoView();
    }""")
    page.wait_for_timeout(500)
    enhance_visible = page.evaluate("""() => {
        const block = document.querySelector('#aiEnhanceBlock');
        return block ? block.style.display !== 'none' : false;
    }""")
    if enhance_visible:
        page.click("#aiEnhanceButton")
        enhance_status = wait_for_enhance(page)
        print(f"  [{preset}] Enhance status: {enhance_status}")
    else:
        print(f"  [{preset}] AI Enhance block not visible, skipping")
        enhance_status = "not_visible"

    # Save aiEnhancedCanvas
    save_canvas_as_png(page, "#aiEnhancedCanvas", preset_dir / "ai_enhanced.png")

    page.screenshot(path=str(preset_dir / "02_after_enhance.png"))

    # Get alpha stats from the final and enhanced canvases
    final_stats = None
    enhanced_stats = None

    final_path = preset_dir / "ai_final.png"
    enhanced_path = preset_dir / "ai_enhanced.png"

    if final_path.exists():
        img = Image.open(final_path)
        final_stats = alpha_stats(img)

    if enhanced_path.exists():
        img = Image.open(enhanced_path)
        enhanced_stats = alpha_stats(img)

    context.close()

    return {
        "preset": preset,
        "status": status,
        "enhance_status": enhance_status,
        "panels": panels,
        "panel_files": [str(p) for p in panel_files],
        "final_stats": final_stats,
        "enhanced_stats": enhanced_stats,
    }


def analyze_references():
    """Load and measure alpha stats for each reference image."""
    ref_stats = {}
    for name, path in REFERENCE_FILES.items():
        img = Image.open(path)
        stats = alpha_stats(img)
        ref_stats[name] = {
            "path": str(path),
            "size": img.size,
            "stats": stats,
        }
    return ref_stats


def match_panels_to_references(preset_result, ref_stats):
    """Try to match test panels to reference images by type."""
    if not preset_result or not preset_result["panel_files"]:
        return {}

    matches = {}
    panels_data = []
    for pf in preset_result["panel_files"]:
        img = Image.open(pf)
        w, h = img.size
        ptype = classify_panel(w, h, 1653, 926)  # ref full-sheet size
        panels_data.append({"path": pf, "img": img, "type": ptype, "size": (w, h)})

    # Find bars (top vs bottom by vertical position -- we just use the first two bars)
    bars = [p for p in panels_data if p["type"] == "bar"]
    portraits = [p for p in panels_data if p["type"] == "portrait_frame"]

    # Sort bars by height (thinner = more likely a bar) and by image content
    if bars:
        # Compare each bar to top_bar and bottom_bar references
        top_ref = Image.open(REFERENCE_FILES["top_bar"])
        bottom_ref = Image.open(REFERENCE_FILES["bottom_bar"])
        for bar in bars:
            top_cmp = compare_images(top_ref, bar["img"])
            bottom_cmp = compare_images(bottom_ref, bar["img"])
            bar["top_score"] = top_cmp["mae_alpha"]
            bar["bottom_score"] = bottom_cmp["mae_alpha"]

        # Assign bars: lower alpha MAE = better match
        for bar in bars:
            if bar["top_score"] < bar["bottom_score"]:
                if "top_bar" not in matches:
                    matches["top_bar"] = bar
            else:
                if "bottom_bar" not in matches:
                    matches["bottom_bar"] = bar

        # If only one bar found, assign whichever is better
        if len(bars) == 1 and not matches:
            bar = bars[0]
            if bar["top_score"] < bar["bottom_score"]:
                matches["top_bar"] = bar
            else:
                matches["bottom_bar"] = bar

    if portraits:
        matches["portrait_frame"] = portraits[0]

    return matches


def print_quality_table(ref_stats, preset_results):
    """Print the quality comparison table."""
    # Determine which stats source to use (enhanced if available, else final)
    def get_stats(result):
        if result and result.get("enhanced_stats"):
            return result["enhanced_stats"]
        if result and result.get("final_stats"):
            return result["final_stats"]
        return None

    # Use the full_sheet reference stats
    ref_full = ref_stats.get("full_sheet", {}).get("stats", {})

    # Count panels info from references (they have 4 reference images)
    ref_panel_types = {"top_bar": True, "bottom_bar": True, "portrait_frame": True}

    print("\n" + "=" * 100)
    print("  QUALITY COMPARISON TABLE")
    print("=" * 100)

    # Header
    header = f"{'Metric':<25} {'Reference':>12}"
    for p in PRESETS:
        header += f" {p:>15}"
    print(header)
    print("-" * len(header))

    # Transparent %
    row = f"{'Transparent%':<25} {ref_full.get('transparent_pct', 'N/A'):>12}"
    for p in PRESETS:
        r = preset_results.get(p)
        s = get_stats(r)
        val = s["transparent_pct"] if s else "FAIL"
        row += f" {str(val):>15}"
    print(row)

    # Semi %
    row = f"{'Semi%':<25} {ref_full.get('semi_pct', 'N/A'):>12}"
    for p in PRESETS:
        r = preset_results.get(p)
        s = get_stats(r)
        val = s["semi_pct"] if s else "FAIL"
        row += f" {str(val):>15}"
    print(row)

    # Opaque %
    row = f"{'Opaque%':<25} {ref_full.get('opaque_pct', 'N/A'):>12}"
    for p in PRESETS:
        r = preset_results.get(p)
        s = get_stats(r)
        val = s["opaque_pct"] if s else "FAIL"
        row += f" {str(val):>15}"
    print(row)

    # Panels found
    ref_panels = 4  # full sheet + 3 individual assets in reference set
    row = f"{'Panels found':<25} {ref_panels:>12}"
    for p in PRESETS:
        r = preset_results.get(p)
        count = len(r["panels"]) if r and r.get("panels") else 0
        row += f" {count:>15}"
    print(row)

    # Likely UI panels
    row = f"{'Likely UI panels':<25} {ref_panels:>12}"
    for p in PRESETS:
        r = preset_results.get(p)
        if r and r.get("panels"):
            count = sum(1 for pp in r["panels"] if pp["isLikelyUi"])
        else:
            count = 0
        row += f" {count:>15}"
    print(row)

    # Panel presence checks
    for panel_type, panel_label in [("top_bar", "Top bar present"), ("bottom_bar", "Bottom bar present"), ("portrait_frame", "Portrait frame present")]:
        row = f"{panel_label:<25} {'Y':>12}"
        for p in PRESETS:
            r = preset_results.get(p)
            if r and r.get("panels"):
                # Check if any panel matches this type
                found = False
                for pp in r["panels"]:
                    pw, ph = 0, 0
                    meta = pp.get("meta", "")
                    if " x " in meta:
                        parts = meta.split(" x ")
                        try:
                            pw, ph = int(parts[0].strip()), int(parts[1].strip())
                        except ValueError:
                            pass
                    ptype = classify_panel(pw, ph, 1653, 926)
                    if panel_type == "top_bar" and ptype == "bar":
                        found = True
                    elif panel_type == "bottom_bar" and ptype == "bar":
                        found = True
                    elif panel_type == "portrait_frame" and ptype == "portrait_frame":
                        found = True
                val = "Y" if found else "N"
            else:
                val = "FAIL"
            row += f" {val:>15}"
        print(row)

    print()


def print_panel_comparison(preset_results, ref_stats):
    """For the best preset, compare panels against references."""
    # Pick the best preset by closest transparent% to reference
    ref_trans = ref_stats.get("full_sheet", {}).get("stats", {}).get("transparent_pct", 0)

    best_preset = None
    best_diff = float("inf")
    for p in PRESETS:
        r = preset_results.get(p)
        if not r:
            continue
        s = r.get("enhanced_stats") or r.get("final_stats")
        if not s:
            continue
        diff = abs(s["transparent_pct"] - ref_trans)
        if diff < best_diff:
            best_diff = diff
            best_preset = p

    if not best_preset:
        print("\n  No valid preset results to compare panels against references.")
        return

    print(f"\n{'=' * 100}")
    print(f"  PANEL-BY-PANEL COMPARISON (best preset: {best_preset})")
    print(f"{'=' * 100}")

    result = preset_results[best_preset]
    matches = match_panels_to_references(result, ref_stats)

    for ref_name, ref_info in ref_stats.items():
        if ref_name == "full_sheet":
            # Compare full-sheet result
            test_path = OUT_DIR / best_preset / "ai_enhanced.png"
            if not test_path.exists():
                test_path = OUT_DIR / best_preset / "ai_final.png"
            if not test_path.exists():
                print(f"\n  {ref_name}: No test result to compare")
                continue
            test_img = Image.open(test_path)
            ref_img = Image.open(ref_info["path"])
            cmp = compare_images(ref_img, test_img)
            print(f"\n  {ref_name} (full extraction):")
            print(f"    Reference size: {cmp['ref_size']}, Test size: {cmp['test_size']}, Same: {cmp['same_size']}")
            print(f"    MAE all channels: {cmp['mae_all_channels']}")
            print(f"    MAE alpha:        {cmp['mae_alpha']}")
            print(f"    Transparent IoU:  {cmp['transparent_iou']}")
            print(f"    Opaque IoU:       {cmp['opaque_iou']}")
        else:
            # Compare individual panels
            match = matches.get(ref_name)
            if not match:
                print(f"\n  {ref_name}: No matching panel found in test results")
                continue
            test_img = match["img"]
            ref_img = Image.open(ref_info["path"])
            cmp = compare_images(ref_img, test_img)
            print(f"\n  {ref_name} (matched to {Path(match['path']).name}):")
            print(f"    Reference size: {cmp['ref_size']}, Test size: {cmp['test_size']}, Same: {cmp['same_size']}")
            print(f"    MAE all channels: {cmp['mae_all_channels']}")
            print(f"    MAE alpha:        {cmp['mae_alpha']}")
            print(f"    Transparent IoU:  {cmp['transparent_iou']}")
            print(f"    Opaque IoU:       {cmp['opaque_iou']}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 100)
    print("  DARK BACKGROUND EXTRACTION QUALITY TEST")
    print("=" * 100)

    # Step 1: Analyze reference images
    print("\n--- Analyzing reference images ---")
    ref_stats = analyze_references()
    for name, info in ref_stats.items():
        s = info["stats"]
        print(f"  {name}: {info['size']} -> "
              f"transparent={s['transparent_pct']}% semi={s['semi_pct']}% opaque={s['opaque_pct']}%")

    # Step 2: Run preset tests via Playwright
    preset_results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for preset in PRESETS:
            print(f"\n{'=' * 60}")
            print(f"  TESTING PRESET: {preset}")
            print(f"{'=' * 60}")
            result = run_preset_test(browser, preset, OUT_DIR)
            if result:
                preset_results[preset] = result
            else:
                print(f"  [{preset}] Test returned no result")
        browser.close()

    # Step 3: Print quality table
    print_quality_table(ref_stats, preset_results)

    # Step 4: Panel-by-panel comparison
    print_panel_comparison(preset_results, ref_stats)

    # Step 5: Save JSON report
    report = {
        "reference_stats": {},
        "preset_results": {},
    }
    for name, info in ref_stats.items():
        report["reference_stats"][name] = {
            "size": list(info["size"]),
            "stats": info["stats"],
        }
    for preset, result in preset_results.items():
        report["preset_results"][preset] = {
            "status": result["status"],
            "enhance_status": result["enhance_status"],
            "panel_count": len(result["panels"]),
            "likely_ui_count": sum(1 for p in result["panels"] if p["isLikelyUi"]),
            "panels": result["panels"],
            "final_stats": result["final_stats"],
            "enhanced_stats": result["enhanced_stats"],
        }
    report_path = OUT_DIR / "quality_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  JSON report saved to: {report_path}")

    # Final summary
    print(f"\n{'=' * 100}")
    print("  FINAL SUMMARY")
    print(f"{'=' * 100}")
    for preset in PRESETS:
        r = preset_results.get(preset)
        if not r:
            print(f"  {preset}: FAILED (no result)")
            continue
        s = r.get("enhanced_stats") or r.get("final_stats")
        panels = r.get("panels", [])
        ui_count = sum(1 for p in panels if p["isLikelyUi"])
        if s:
            print(f"  {preset}: trans={s['transparent_pct']}% semi={s['semi_pct']}% opaque={s['opaque_pct']}% "
                  f"panels={len(panels)} ui_panels={ui_count}")
        else:
            print(f"  {preset}: no stats, panels={len(panels)}")

    ref_full = ref_stats.get("full_sheet", {}).get("stats", {})
    print(f"  Reference: trans={ref_full.get('transparent_pct')}% semi={ref_full.get('semi_pct')}% opaque={ref_full.get('opaque_pct')}%")

    print(f"\n  All output saved to: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
