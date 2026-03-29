"""
Comprehensive quality test for ALL presets against reference images.

Dark presets (dark-balanced, dark-soft, dark-hard) use AI Remove mode.
Light presets (light-balanced, light-soft, light-hard) use heuristic Process Image mode.

Usage:
    .venv/Scripts/python.exe tests/test_quality_final.py
"""

import base64
import json
import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

# ── Config ────────────────────────────────────────────────────────────
ROOT = Path(r"C:\Dev\Image generator")
APP_URL = "http://127.0.0.1:8080"
OUT_DIR = ROOT / "test_screenshots" / "quality_final"

DARK_DIR = ROOT / "input" / "Example quality image extraction" / "Dark background examples"
LIGHT_DIR = ROOT / "input" / "Example quality image extraction" / "Light background examples"

DARK_SOURCE = DARK_DIR / "Original Image dark background.png"
DARK_REF = DARK_DIR / "example preview ectraction dark background removed.PNG"

LIGHT_SOURCE = LIGHT_DIR / "Original Image White background.png"
LIGHT_REF = LIGHT_DIR / "example preview ectraction white background removed.PNG"

DARK_PRESETS = ["dark-balanced", "dark-soft", "dark-hard"]
LIGHT_PRESETS = ["light-balanced", "light-soft", "light-hard"]


# ── Alpha helpers ─────────────────────────────────────────────────────

def alpha_stats(img):
    """Return transparent/semi/opaque percentages for an RGBA image."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    total = alpha.size
    transparent = float(np.sum(alpha == 0)) / total * 100
    opaque = float(np.sum(alpha == 255)) / total * 100
    semi = 100.0 - transparent - opaque
    return {
        "transparent": round(transparent, 2),
        "semi": round(semi, 2),
        "opaque": round(opaque, 2),
    }


def region_opaque_pct(img, x_start, x_end, y_start, y_end):
    """Return % of opaque pixels in a sub-region (fractions of image size)."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]
    y0 = int(h * y_start)
    y1 = int(h * y_end)
    x0 = int(w * x_start)
    x1 = int(w * x_end)
    region = arr[y0:y1, x0:x1, 3]
    if region.size == 0:
        return 0.0
    return round(float(np.sum(region > 128)) / region.size * 100, 2)


def pixel_diff_count(img_a, img_b):
    """Count pixels that differ between two RGBA images (same size assumed)."""
    a = np.array(img_a.convert("RGBA"))
    b = np.array(img_b.convert("RGBA"))
    if a.shape != b.shape:
        # Resize b to match a
        img_b_r = img_b.resize((img_a.width, img_a.height), Image.LANCZOS)
        b = np.array(img_b_r.convert("RGBA"))
    diff = np.any(a != b, axis=2)
    return int(np.sum(diff))


def compare_vs_ref(test_img, ref_img):
    """Return alpha MAE and transparent IoU vs reference."""
    if test_img.size != ref_img.size:
        test_img = test_img.resize(ref_img.size, Image.LANCZOS)
    t_alpha = np.array(test_img.convert("RGBA"))[:, :, 3].astype(float)
    r_alpha = np.array(ref_img.convert("RGBA"))[:, :, 3].astype(float)
    mae = float(np.mean(np.abs(t_alpha - r_alpha)))
    # IoU of transparent regions
    t_trans = t_alpha < 10
    r_trans = r_alpha < 10
    intersection = float(np.sum(t_trans & r_trans))
    union = float(np.sum(t_trans | r_trans))
    iou = intersection / max(1, union)
    return {"alpha_mae": round(mae, 2), "trans_iou": round(iou, 4)}


# ── Canvas extraction ─────────────────────────────────────────────────

def save_canvas(page, canvas_id_or_js, out_path):
    """Extract a canvas element as PNG. Returns PIL Image or None."""
    if canvas_id_or_js.startswith("("):
        # JS expression
        data_url = page.evaluate(canvas_id_or_js)
    else:
        data_url = page.evaluate(f"""() => {{
            const c = document.querySelector('{canvas_id_or_js}');
            if (!c || c.width <= 1 || c.height <= 1) return null;
            return c.toDataURL('image/png');
        }}""")
    if not data_url:
        return None
    header = "data:image/png;base64,"
    if not data_url.startswith(header):
        return None
    raw = base64.b64decode(data_url[len(header):])
    with open(out_path, "wb") as f:
        f.write(raw)
    return Image.open(BytesIO(raw)).convert("RGBA")


def save_processed_layout(page, out_path):
    """Extract processedLayoutCanvas (JS global variable)."""
    return save_canvas(page, """() => {
        if (typeof processedLayoutCanvas === 'undefined' || !processedLayoutCanvas) return null;
        if (processedLayoutCanvas.width <= 1) return null;
        return processedLayoutCanvas.toDataURL('image/png');
    }""", out_path)


# ── Wait helpers ──────────────────────────────────────────────────────

def wait_ai_remove(page, timeout=90):
    """Wait for AI Remove to finish (poll status/button)."""
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
        # Check button re-enabled with result canvas populated
        btn_dis = page.evaluate("() => document.querySelector('#aiRemoveButton')?.disabled")
        if not btn_dis and time.time() - start > 5:
            sz = page.evaluate("() => { const c = document.querySelector('#resultCanvas'); return c ? c.width : 0; }")
            if sz > 1:
                return status or "completed"
        time.sleep(2)
    return "TIMEOUT"


def wait_process(page, timeout=30):
    """Wait for heuristic Process Image to finish."""
    start = time.time()
    while time.time() - start < timeout:
        status = page.text_content("#bgStatus") or ""
        if "Done." in status:
            return status
        if "failed" in status.lower() or "error" in status.lower():
            return f"FAIL: {status}"
        time.sleep(0.5)
    return "TIMEOUT"


def wait_enhance(page, timeout=15):
    """Wait for AI Enhance to finish."""
    start = time.time()
    while time.time() - start < timeout:
        status = page.evaluate("""() => {
            const el = document.querySelector('#aiEnhanceStatus');
            return el ? el.textContent : '';
        }""")
        if "complete" in status.lower() or "compare" in status.lower():
            return status
        time.sleep(1)
    return "TIMEOUT"


# ── Test runners ──────────────────────────────────────────────────────

def run_dark_preset(browser, preset, source_path, out_dir):
    """Run a dark preset test using AI Remove mode."""
    tag = preset.replace("-", "_")
    preset_dir = out_dir / tag
    preset_dir.mkdir(parents=True, exist_ok=True)

    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.goto(APP_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)

    # Load image
    print(f"  [{preset}] Loading source image...")
    page.set_input_files("#bgInputFile", str(source_path))
    page.wait_for_timeout(3000)

    # Open advanced settings and select preset
    page.evaluate('() => document.querySelectorAll(".card.closed").forEach(c => c.classList.remove("closed"))')
    page.wait_for_timeout(500)
    page.select_option("#bgPreset", preset)
    page.wait_for_timeout(500)

    # Click AI Remove
    print(f"  [{preset}] Running AI Remove...")
    page.click("#aiRemoveButton")
    status = wait_ai_remove(page, timeout=90)
    print(f"  [{preset}] AI Remove status: {status}")
    page.screenshot(path=str(preset_dir / "01_after_ai_remove.png"))

    if "FAIL" in status or "TIMEOUT" in status:
        print(f"  [{preset}] FAILED: {status}")
        ctx.close()
        return {"preset": preset, "status": status, "error": True}

    # Extract canvases before enhance
    final_img = save_canvas(page, "#aiFinalCanvas", preset_dir / "ai_final.png")
    layout_img = save_processed_layout(page, preset_dir / "processed_layout.png")

    # Run AI Enhance
    print(f"  [{preset}] Running AI Enhance...")
    page.evaluate("() => { const b = document.querySelector('#aiEnhanceButton'); if(b) b.scrollIntoView(); }")
    page.wait_for_timeout(500)
    enhance_visible = page.evaluate("() => { const b = document.querySelector('#aiEnhanceBlock'); return b ? b.style.display !== 'none' : false; }")
    enhanced_img = None
    if enhance_visible:
        page.click("#aiEnhanceButton")
        page.wait_for_timeout(5000)
        enhance_status = wait_enhance(page, timeout=15)
        print(f"  [{preset}] Enhance status: {enhance_status}")
        enhanced_img = save_canvas(page, "#aiEnhancedCanvas", preset_dir / "ai_enhanced.png")
    else:
        print(f"  [{preset}] Enhance block not visible")

    page.screenshot(path=str(preset_dir / "02_final.png"))
    ctx.close()

    return {
        "preset": preset,
        "status": status,
        "error": False,
        "final_img": final_img,
        "enhanced_img": enhanced_img,
        "layout_img": layout_img,
    }


def run_light_preset(browser, preset, source_path, out_dir):
    """Run a light preset test using heuristic Process Image mode."""
    tag = preset.replace("-", "_")
    preset_dir = out_dir / tag
    preset_dir.mkdir(parents=True, exist_ok=True)

    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.goto(APP_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)

    # Load image
    print(f"  [{preset}] Loading source image...")
    page.set_input_files("#bgInputFile", str(source_path))
    page.wait_for_timeout(3000)

    # Open advanced settings
    page.evaluate('() => document.querySelectorAll(".card.closed").forEach(c => c.classList.remove("closed"))')
    page.wait_for_timeout(500)

    # Select preset
    page.select_option("#bgPreset", preset)
    page.wait_for_timeout(500)

    # Click Process Image (heuristic mode)
    print(f"  [{preset}] Running Process Image...")
    page.click("#processBgButton")
    status = wait_process(page, timeout=30)
    print(f"  [{preset}] Process status: {status}")
    page.screenshot(path=str(preset_dir / "01_after_process.png"))

    if "FAIL" in status or "TIMEOUT" in status:
        print(f"  [{preset}] FAILED: {status}")
        ctx.close()
        return {"preset": preset, "status": status, "error": True}

    # Heuristic mode writes to resultCanvas and processedLayoutCanvas (not aiFinalCanvas)
    result_img = save_canvas(page, "#resultCanvas", preset_dir / "result_canvas.png")
    layout_img = save_processed_layout(page, preset_dir / "processed_layout.png")
    print(f"  [{preset}] result_canvas: {'OK' if result_img else 'EMPTY'}  layout: {'OK' if layout_img else 'EMPTY'}")

    # AI Enhance is only available after AI Remove, not heuristic mode
    print(f"  [{preset}] Checking AI Enhance availability...")
    page.evaluate("() => { const b = document.querySelector('#aiEnhanceButton'); if(b) b.scrollIntoView(); }")
    page.wait_for_timeout(500)
    enhance_visible = page.evaluate("() => { const b = document.querySelector('#aiEnhanceBlock'); return b ? b.style.display !== 'none' : false; }")
    enhanced_img = None
    if enhance_visible:
        page.click("#aiEnhanceButton")
        page.wait_for_timeout(5000)
        enhance_status = wait_enhance(page, timeout=15)
        print(f"  [{preset}] Enhance status: {enhance_status}")
        enhanced_img = save_canvas(page, "#aiEnhancedCanvas", preset_dir / "ai_enhanced.png")
    else:
        print(f"  [{preset}] Enhance block not visible (expected for heuristic mode)")

    page.screenshot(path=str(preset_dir / "02_final.png"))
    ctx.close()

    return {
        "preset": preset,
        "status": status,
        "error": False,
        "final_img": layout_img or result_img,
        "enhanced_img": enhanced_img,
        "layout_img": layout_img,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Measure reference images ──────────────────────────────────────
    print("=" * 90)
    print("  REFERENCE IMAGE ANALYSIS")
    print("=" * 90)

    dark_ref_img = Image.open(DARK_REF).convert("RGBA")
    light_ref_img = Image.open(LIGHT_REF).convert("RGBA")
    dark_ref_stats = alpha_stats(dark_ref_img)
    light_ref_stats = alpha_stats(light_ref_img)

    print(f"  Dark  ref: {dark_ref_img.size}  trans={dark_ref_stats['transparent']}%  semi={dark_ref_stats['semi']}%  opaque={dark_ref_stats['opaque']}%")
    print(f"  Light ref: {light_ref_img.size}  trans={light_ref_stats['transparent']}%  semi={light_ref_stats['semi']}%  opaque={light_ref_stats['opaque']}%")

    # Region checks on dark reference
    dark_ref_topbar = region_opaque_pct(dark_ref_img, 0, 1, 0, 0.10)
    dark_ref_botbar = region_opaque_pct(dark_ref_img, 0, 1, 0.70, 1.0)
    dark_ref_portrait = region_opaque_pct(dark_ref_img, 0, 0.10, 0.60, 1.0)
    print(f"  Dark ref regions: TopBar={dark_ref_topbar}%  BotBar={dark_ref_botbar}%  Portrait={dark_ref_portrait}%")

    # ── Run tests ─────────────────────────────────────────────────────
    dark_results = {}
    light_results = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # Dark presets
        for preset in DARK_PRESETS:
            print(f"\n{'=' * 70}")
            print(f"  DARK TEST: {preset}")
            print(f"{'=' * 70}")
            result = run_dark_preset(browser, preset, DARK_SOURCE, OUT_DIR)
            dark_results[preset] = result

        # Light presets
        for preset in LIGHT_PRESETS:
            print(f"\n{'=' * 70}")
            print(f"  LIGHT TEST: {preset}")
            print(f"{'=' * 70}")
            result = run_light_preset(browser, preset, LIGHT_SOURCE, OUT_DIR)
            light_results[preset] = result

        browser.close()

    # ── Compute metrics ───────────────────────────────────────────────
    print("\n\n")
    print("=" * 120)
    print("  DARK BACKGROUND RESULTS")
    print("=" * 120)
    header = f"| {'Preset':<16} | {'Trans%':>8} | {'Semi%':>8} | {'Opaque%':>8} | {'TopBar':>8} | {'BotBar':>8} | {'Portrait':>8} | {'Enh Diff':>10} | {'vs Ref MAE':>10} | {'vs Ref IoU':>10} |"
    sep = "|" + "-" * 18 + "|" + ("-" * 10 + "|") * 8
    print(header)
    print(sep)

    # Reference row
    print(f"| {'REF':.<16} | {dark_ref_stats['transparent']:>8.2f} | {dark_ref_stats['semi']:>8.2f} | {dark_ref_stats['opaque']:>8.2f} | {dark_ref_topbar:>8.2f} | {dark_ref_botbar:>8.2f} | {dark_ref_portrait:>8.2f} | {'---':>10} | {'---':>10} | {'---':>10} |")

    for preset in DARK_PRESETS:
        r = dark_results[preset]
        if r.get("error"):
            print(f"| {preset:<16} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>10} | {'FAIL':>10} | {'FAIL':>10} |")
            continue

        # Pick best available image: enhanced > final > layout
        best_img = r.get("enhanced_img") or r.get("final_img") or r.get("layout_img")
        if not best_img:
            print(f"| {preset:<16} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>10} | {'NO IMG':>10} | {'NO IMG':>10} |")
            continue

        stats = alpha_stats(best_img)
        topbar = region_opaque_pct(best_img, 0, 1, 0, 0.10)
        botbar = region_opaque_pct(best_img, 0, 1, 0.70, 1.0)
        portrait = region_opaque_pct(best_img, 0, 0.10, 0.60, 1.0)

        # Enhance diff
        enh_diff = "---"
        if r.get("enhanced_img") and r.get("final_img"):
            enh_diff = str(pixel_diff_count(r["final_img"], r["enhanced_img"]))

        # Vs reference
        cmp = compare_vs_ref(best_img, dark_ref_img)

        print(f"| {preset:<16} | {stats['transparent']:>8.2f} | {stats['semi']:>8.2f} | {stats['opaque']:>8.2f} | {topbar:>8.2f} | {botbar:>8.2f} | {portrait:>8.2f} | {enh_diff:>10} | {cmp['alpha_mae']:>10.2f} | {cmp['trans_iou']:>10.4f} |")

    # Light results
    print("\n\n")
    print("=" * 100)
    print("  LIGHT BACKGROUND RESULTS")
    print("=" * 100)
    header_l = f"| {'Preset':<16} | {'Trans%':>8} | {'Semi%':>8} | {'Opaque%':>8} | {'Enh Diff':>10} | {'vs Ref MAE':>10} | {'vs Ref IoU':>10} |"
    sep_l = "|" + "-" * 18 + "|" + ("-" * 10 + "|") * 5
    print(header_l)
    print(sep_l)

    # Reference row
    print(f"| {'REF':.<16} | {light_ref_stats['transparent']:>8.2f} | {light_ref_stats['semi']:>8.2f} | {light_ref_stats['opaque']:>8.2f} | {'---':>10} | {'---':>10} | {'---':>10} |")

    for preset in LIGHT_PRESETS:
        r = light_results[preset]
        if r.get("error"):
            print(f"| {preset:<16} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>8} | {'FAIL':>10} | {'FAIL':>10} | {'FAIL':>10} |")
            continue

        best_img = r.get("enhanced_img") or r.get("final_img") or r.get("layout_img")
        if not best_img:
            print(f"| {preset:<16} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>8} | {'NO IMG':>10} | {'NO IMG':>10} | {'NO IMG':>10} |")
            continue

        stats = alpha_stats(best_img)

        enh_diff = "---"
        if r.get("enhanced_img") and r.get("final_img"):
            enh_diff = str(pixel_diff_count(r["final_img"], r["enhanced_img"]))

        cmp = compare_vs_ref(best_img, light_ref_img)

        print(f"| {preset:<16} | {stats['transparent']:>8.2f} | {stats['semi']:>8.2f} | {stats['opaque']:>8.2f} | {enh_diff:>10} | {cmp['alpha_mae']:>10.2f} | {cmp['trans_iou']:>10.4f} |")

    # ── Save JSON report ──────────────────────────────────────────────
    report = {
        "dark_reference": dark_ref_stats,
        "light_reference": light_ref_stats,
        "dark_results": {},
        "light_results": {},
    }
    for preset in DARK_PRESETS:
        r = dark_results[preset]
        best_img = r.get("enhanced_img") or r.get("final_img") or r.get("layout_img")
        entry = {"status": r.get("status", ""), "error": r.get("error", False)}
        if best_img:
            entry["stats"] = alpha_stats(best_img)
            entry["vs_ref"] = compare_vs_ref(best_img, dark_ref_img)
            entry["topbar"] = region_opaque_pct(best_img, 0, 1, 0, 0.10)
            entry["botbar"] = region_opaque_pct(best_img, 0, 1, 0.70, 1.0)
            entry["portrait"] = region_opaque_pct(best_img, 0, 0.10, 0.60, 1.0)
        report["dark_results"][preset] = entry

    for preset in LIGHT_PRESETS:
        r = light_results[preset]
        best_img = r.get("enhanced_img") or r.get("final_img") or r.get("layout_img")
        entry = {"status": r.get("status", ""), "error": r.get("error", False)}
        if best_img:
            entry["stats"] = alpha_stats(best_img)
            entry["vs_ref"] = compare_vs_ref(best_img, light_ref_img)
        report["light_results"][preset] = entry

    report_path = OUT_DIR / "quality_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  JSON report saved to: {report_path}")
    print(f"  All output images saved to: {OUT_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
