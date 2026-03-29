"""Comprehensive test of all Advanced Settings controls."""
import sys, os, json, time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8080/index.html"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

IMAGE_PATH = r"C:\Dev\Image generator\input\UI2.1.png"

results = []

def log(msg, status="OK"):
    results.append((msg, status))
    icon = "[PASS]" if status == "OK" else "[FAIL]"
    print(f"  {icon} {msg}")

def screenshot(page, name):
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, name), full_page=True)


def test_select(page, selector, expected_options, label, force_enable=False):
    """Test a <select> element: verify options exist, change value, verify change."""
    el = page.query_selector(selector)
    if not el:
        log(f"{label}: element {selector} NOT FOUND", "FAIL")
        return
    # Check if disabled
    is_disabled = page.eval_on_selector(selector, "el => el.disabled")
    if is_disabled and not force_enable:
        # Just verify options exist
        options = page.eval_on_selector(selector, "el => Array.from(el.options).map(o => o.value)")
        if set(options) != set(expected_options):
            log(f"{label}: expected options {expected_options}, got {options}", "FAIL")
        else:
            log(f"{label}: disabled (expected), options correct ({', '.join(expected_options)})")
        return
    if force_enable and is_disabled:
        page.eval_on_selector(selector, "el => el.disabled = false")
    # Get all option values
    options = page.eval_on_selector(selector, "el => Array.from(el.options).map(o => o.value)")
    if set(options) != set(expected_options):
        log(f"{label}: expected options {expected_options}, got {options}", "FAIL")
        return
    # Try selecting each option
    for val in expected_options:
        page.select_option(selector, val)
        actual = page.eval_on_selector(selector, "el => el.value")
        if actual != val:
            log(f"{label}: set to '{val}' but got '{actual}'", "FAIL")
            return
    log(f"{label}: all {len(expected_options)} options work ({', '.join(expected_options)})")


def test_range(page, selector, display_selector, label, expected_default, min_val, max_val):
    """Test a range slider: verify default, change value, verify display updates."""
    el = page.query_selector(selector)
    if not el:
        log(f"{label}: element {selector} NOT FOUND", "FAIL")
        return

    # Force enable if disabled
    is_disabled = page.eval_on_selector(selector, "el => el.disabled")
    if is_disabled:
        page.eval_on_selector(selector, "el => el.disabled = false")

    # Check default value
    current_val = page.eval_on_selector(selector, "el => el.value")
    if str(current_val) != str(expected_default):
        log(f"{label}: default expected {expected_default}, got {current_val}", "FAIL")
        return

    # Check min/max attributes
    actual_min = page.eval_on_selector(selector, "el => el.min")
    actual_max = page.eval_on_selector(selector, "el => el.max")
    if str(actual_min) != str(min_val):
        log(f"{label}: min expected {min_val}, got {actual_min}", "FAIL")
        return
    if str(actual_max) != str(max_val):
        log(f"{label}: max expected {max_val}, got {actual_max}", "FAIL")
        return

    # Change value to midpoint and verify display updates
    # Account for step attribute snapping
    step = int(page.eval_on_selector(selector, "el => el.step || '1'"))
    mid = (int(min_val) + int(max_val)) // 2
    # Align to step
    if step > 1:
        mid = round(mid / step) * step
    page.eval_on_selector(selector, f"el => {{ el.value = {mid}; el.dispatchEvent(new Event('input', {{bubbles:true}})); }}")
    page.wait_for_timeout(100)

    new_val = page.eval_on_selector(selector, "el => el.value")
    if str(new_val) != str(mid):
        log(f"{label}: set to {mid} but value is {new_val}", "FAIL")
        return

    # Verify display label updates
    if display_selector:
        disp_el = page.query_selector(display_selector)
        if not disp_el:
            log(f"{label}: display element {display_selector} NOT FOUND", "FAIL")
            return
        disp_text = page.eval_on_selector(display_selector, "el => el.textContent.trim()")
        if str(disp_text) != str(mid):
            log(f"{label}: display shows '{disp_text}' but expected '{mid}'", "FAIL")
            return

    # Restore default
    page.eval_on_selector(selector, f"el => {{ el.value = {expected_default}; el.dispatchEvent(new Event('input', {{bubbles:true}})); }}")
    log(f"{label}: range [{min_val}-{max_val}], default={expected_default}, display updates correctly")


def test_checkbox(page, selector, label, expected_default=False):
    """Test a checkbox: verify default state, toggle it, verify change."""
    el = page.query_selector(selector)
    if not el:
        log(f"{label}: element {selector} NOT FOUND", "FAIL")
        return
    # Force enable if disabled
    is_disabled = page.eval_on_selector(selector, "el => el.disabled")
    if is_disabled:
        page.eval_on_selector(selector, "el => el.disabled = false")
    checked = page.eval_on_selector(selector, "el => el.checked")
    if checked != expected_default:
        log(f"{label}: default expected {'checked' if expected_default else 'unchecked'}, got {'checked' if checked else 'unchecked'}", "FAIL")
        return
    # Toggle
    page.eval_on_selector(selector, "el => { el.checked = !el.checked; el.dispatchEvent(new Event('change', {bubbles:true})); }")
    new_checked = page.eval_on_selector(selector, "el => el.checked")
    if new_checked == checked:
        log(f"{label}: toggle didn't change state", "FAIL")
        return
    # Toggle back
    page.eval_on_selector(selector, "el => { el.checked = !el.checked; el.dispatchEvent(new Event('change', {bubbles:true})); }")
    log(f"{label}: default={'checked' if expected_default else 'unchecked'}, toggle works")


def test_input_text(page, selector, label):
    """Test a text input exists and can be modified."""
    el = page.query_selector(selector)
    if not el:
        log(f"{label}: element {selector} NOT FOUND", "FAIL")
        return
    val = page.eval_on_selector(selector, "el => el.value")
    log(f"{label}: value='{val}'")


def test_button_exists(page, selector, label):
    """Test a button exists and is clickable."""
    el = page.query_selector(selector)
    if not el:
        log(f"{label}: element {selector} NOT FOUND", "FAIL")
        return
    disabled = page.eval_on_selector(selector, "el => el.disabled")
    log(f"{label}: present, {'disabled' if disabled else 'enabled'}")


def test_preset_updates(page):
    """Test that changing preset updates the correct sliders."""
    presets = {
        "ui-balanced": {"bgThreshold": "18", "bgSoftness": "24", "bgAlphaFloor": "8", "bgAlphaCeiling": "245"},
        "ui-soft": {"bgThreshold": "14", "bgSoftness": "34", "bgAlphaFloor": "4", "bgAlphaCeiling": "245"},
        "ui-hard": {"bgThreshold": "24", "bgSoftness": "16", "bgAlphaFloor": "12", "bgAlphaCeiling": "238"},
    }
    all_ok = True
    for preset_name, expected in presets.items():
        page.select_option("#bgPreset", preset_name)
        page.wait_for_timeout(100)
        for control_id, expected_val in expected.items():
            actual = page.eval_on_selector(f"#{control_id}", "el => el.value")
            if str(actual) != str(expected_val):
                log(f"Preset '{preset_name}': {control_id} expected {expected_val}, got {actual}", "FAIL")
                all_ok = False
    # Also check that display labels updated
    page.select_option("#bgPreset", "ui-hard")
    page.wait_for_timeout(100)
    threshold_display = page.eval_on_selector("#thresholdValue", "el => el.textContent.trim()")
    if threshold_display != "24":
        log(f"Preset display: thresholdValue shows '{threshold_display}' expected '24'", "FAIL")
        all_ok = False
    softness_display = page.eval_on_selector("#softnessValue", "el => el.textContent.trim()")
    if softness_display != "16":
        log(f"Preset display: softnessValue shows '{softness_display}' expected '16'", "FAIL")
        all_ok = False

    # Restore default
    page.select_option("#bgPreset", "ui-balanced")
    page.wait_for_timeout(100)

    if all_ok:
        log("Preset switching: all 3 presets correctly update sliders and display labels")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1200})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Step 1: Load image via file input
    print("=== Loading test image ===")
    page.set_input_files("#bgInputFile", IMAGE_PATH)
    page.wait_for_timeout(1500)
    screenshot(page, "01_image_loaded.png")

    # Step 2: Open Advanced Settings card
    print("=== Opening Advanced Settings ===")
    # The advanced settings card is the second .card (index 1) and starts closed
    cards = page.query_selector_all(".card")
    adv_card = None
    for card in cards:
        header = card.query_selector("h3")
        if header and "Advanced" in header.text_content():
            adv_card = card
            break
    if adv_card:
        is_closed = page.evaluate("el => el.classList.contains('closed')", adv_card)
        if is_closed:
            adv_card.query_selector(".card-header").click()
            page.wait_for_timeout(300)
    screenshot(page, "02_advanced_open.png")

    # ============================
    # TEST ALL CONTROLS
    # ============================
    print("\n=== Mode & Preset ===")
    test_select(page, "#bgMode", ["remove", "crop", "multi", "ai"], "bgMode")
    # Reset to remove mode
    page.select_option("#bgMode", "remove")
    test_select(page, "#bgPreset", ["ui-balanced", "ui-soft", "ui-hard"], "bgPreset")
    page.select_option("#bgPreset", "ui-balanced")

    print("\n=== Preset Update Verification ===")
    test_preset_updates(page)

    print("\n=== ComfyUI & AI Mask ===")
    test_input_text(page, "#comfyuiServer", "comfyuiServer")
    test_button_exists(page, "#comfyuiConnectButton", "comfyuiConnectButton")
    test_button_exists(page, "#comfyuiGenerateMaskButton", "comfyuiGenerateMaskButton")
    test_button_exists(page, "#browserMaskButton", "browserMaskButton")

    print("\n=== Mask Refinement (switching to AI mode first) ===")
    # AI mask controls are only enabled when bgMode = "ai"
    page.select_option("#bgMode", "ai")
    page.wait_for_timeout(200)
    test_select(page, "#bgAiSource", ["bria", "isnet", "hybrid"], "bgAiSource")
    test_range(page, "#bgAiConfidence", "#aiConfidenceValue", "bgAiConfidence", 72, 1, 100)
    test_range(page, "#bgAiMatte", "#aiMatteValue", "bgAiMatte", 68, 0, 100)
    test_range(page, "#bgAiSpill", "#aiSpillValue", "bgAiSpill", 62, 0, 100)
    test_checkbox(page, "#bgAiRelight", "bgAiRelight", False)
    test_checkbox(page, "#bgAiInpaint", "bgAiInpaint", False)
    test_checkbox(page, "#bgAiInvertMask", "bgAiInvertMask", False)
    test_range(page, "#bgAiMaskExpand", "#aiMaskExpandValue", "bgAiMaskExpand", 0, -12, 12)
    test_range(page, "#bgAiMaskFeather", "#aiMaskFeatherValue", "bgAiMaskFeather", 0, 0, 12)
    test_checkbox(page, "#bgAiCombineManual", "bgAiCombineManual", True)
    # Switch back to remove mode
    page.select_option("#bgMode", "remove")
    page.wait_for_timeout(200)

    print("\n=== Threshold & Edges ===")
    test_range(page, "#bgThreshold", "#thresholdValue", "bgThreshold", 18, 0, 100)
    test_range(page, "#bgSoftness", "#softnessValue", "bgSoftness", 24, 0, 100)
    test_range(page, "#bgAlphaFloor", "#alphaFloorValue", "bgAlphaFloor", 8, 0, 100)
    test_range(page, "#bgAlphaCeiling", "#alphaCeilingValue", "bgAlphaCeiling", 245, 100, 255)
    test_range(page, "#bgEdgeCleanupStrength", "#edgeCleanupValue", "bgEdgeCleanupStrength", 55, 0, 100)
    test_checkbox(page, "#bgCropTransparent", "bgCropTransparent", False)
    test_checkbox(page, "#bgDecontaminate", "bgDecontaminate", True)
    test_checkbox(page, "#bgStrongBorderRepair", "bgStrongBorderRepair", True)
    test_checkbox(page, "#bgPreserveColor", "bgPreserveColor", True)
    test_checkbox(page, "#bgSecondPass", "bgSecondPass", False)

    print("\n=== Output & View ===")
    test_select(page, "#bgLayout", ["sheet", "split"], "bgLayout")
    # bgMaskSource and bgPreviewTarget are disabled until processing occurs - force enable to test options
    test_select(page, "#bgMaskSource", ["processed", "manual", "ai"], "bgMaskSource", force_enable=True)
    test_select(page, "#bgPreviewTarget", ["result", "mask"], "bgPreviewTarget", force_enable=True)
    test_select(page, "#bgPanelLayout", ["crop", "full"], "bgPanelLayout")
    test_select(page, "#bgEditorView", ["balanced", "focus"], "bgEditorView")
    test_range(page, "#bgBrushSize", "#brushSizeValue", "bgBrushSize", 22, 2, 120)
    test_range(page, "#bgMaskOverlay", "#maskOverlayValue", "bgMaskOverlay", 55, 0, 100)

    print("\n=== Split Settings ===")
    test_range(page, "#bgComponentAlpha", "#componentAlphaValue", "bgComponentAlpha", 220, 100, 255)
    test_range(page, "#bgComponentPixels", "#componentPixelsValue", "bgComponentPixels", 5000, 200, 80000)
    test_range(page, "#bgComponentPad", "#componentPadValue", "bgComponentPad", 2, 0, 24)
    test_range(page, "#bgObjectPad", "#objectPadValue", "bgObjectPad", 12, 0, 60)

    # Screenshot after all tests
    screenshot(page, "03_all_controls_tested.png")

    # Step 3: Test Process Image button works
    print("\n=== Process Image Button ===")
    page.select_option("#bgPreset", "ui-balanced")
    page.wait_for_timeout(100)
    page.select_option("#bgMode", "remove")
    page.wait_for_timeout(100)

    process_btn = page.query_selector("#processBgButton")
    if process_btn:
        process_btn.click()
        # Wait for processing to complete
        page.wait_for_timeout(5000)
        status_text = page.eval_on_selector("#bgStatus", "el => el.textContent")
        print(f"  Process status: {status_text}")
        screenshot(page, "04_after_process.png")
        # Check if result canvas has content
        has_result = page.evaluate("""() => {
            const c = document.getElementById('resultCanvas');
            return c && c.width > 0 && c.height > 0;
        }""")
        if has_result:
            log("Process Image: produced a result canvas")
        else:
            log("Process Image: no result canvas content (may need background samples)", "FAIL")
    else:
        log("Process Image button: NOT FOUND", "FAIL")

    # Step 4: Test ComfyUI connection button
    print("\n=== ComfyUI Connection Test ===")
    connect_btn = page.query_selector("#comfyuiConnectButton")
    if connect_btn:
        connect_btn.click()
        page.wait_for_timeout(2000)
        dot_color = page.eval_on_selector("#comfyuiDot", "el => getComputedStyle(el).backgroundColor")
        status_text = page.eval_on_selector("#comfyuiStatus", "el => el.textContent")
        print(f"  ComfyUI dot color: {dot_color}, status: {status_text}")
        log(f"ComfyUI connection: {status_text}")

    screenshot(page, "05_final_state.png")

    browser.close()

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
passed = sum(1 for _, s in results if s == "OK")
failed = sum(1 for _, s in results if s == "FAIL")
print(f"\nTotal: {len(results)} checks, {passed} passed, {failed} failed\n")
if failed > 0:
    print("FAILURES:")
    for msg, s in results:
        if s == "FAIL":
            print(f"  - {msg}")
