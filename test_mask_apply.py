"""Test: load the mask in a browser context and check what alphaFromMaskCanvas returns."""
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto("http://127.0.0.1:8080/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    # Upload source image
    page.set_input_files("#bgInputFile", os.path.abspath("C:/Dev/Image generator/input/Example UI 1.png"))
    page.wait_for_timeout(1000)

    # Generate AI mask
    page.click("#comfyuiGenerateMaskButton")
    page.wait_for_timeout(25000)

    # Debug: check importedAiMaskAlpha values
    result = page.evaluate("""() => {
        if (!importedAiMaskAlpha) return {error: "importedAiMaskAlpha is null"};
        let zeros = 0, mid = 0, full = 0;
        for (let i = 0; i < importedAiMaskAlpha.length; i++) {
            if (importedAiMaskAlpha[i] === 0) zeros++;
            else if (importedAiMaskAlpha[i] === 255) full++;
            else mid++;
        }
        return {
            length: importedAiMaskAlpha.length,
            zeros: zeros,
            mid: mid,
            full: full,
            sample10: Array.from(importedAiMaskAlpha.slice(0, 10)),
            sampleMid: Array.from(importedAiMaskAlpha.slice(Math.floor(importedAiMaskAlpha.length/2), Math.floor(importedAiMaskAlpha.length/2)+10)),
            maskSource: bgMaskSource ? bgMaskSource.value : "unknown",
            mode: bgMode ? bgMode.value : "unknown",
            aiMaskCanvasExists: !!aiMaskCanvas,
            invertChecked: bgAiInvertMask ? bgAiInvertMask.checked : false
        };
    }""")
    print("importedAiMaskAlpha analysis:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Now try processing
    page.click("#processBgButton")
    page.wait_for_timeout(5000)

    # Check status
    status = page.evaluate("() => bgStatus ? bgStatus.textContent : 'no status'")
    print(f"\nStatus after process: {status}")

    page.screenshot(path="test_mask_result.png", full_page=False)
    browser.close()
    print("Screenshot saved to test_mask_result.png")
