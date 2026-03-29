"""Test AI mode edge protection + local spill cleanup with a simulated AI mask."""
import sys
import os
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
source_path = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
reference_path = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else None
output_dir = sys.argv[4] if len(sys.argv) > 4 else "test_screenshots"

os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Step 1: Load the source image
    if source_path:
        print(f"Loading source: {source_path}")
        with page.expect_file_chooser() as fc_info:
            page.click("#bgInputFile")
        fc_info.value.set_files(source_path)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(output_dir, "ai_00_loaded.png"), full_page=True)
        print("Source loaded.")

    # Step 2: Inject a simulated AI mask from the reference image
    # The reference has white where background should be removed.
    # We'll create a mask: white in reference -> alpha=0 (remove), non-white -> alpha=255 (keep)
    if reference_path:
        print(f"Creating simulated AI mask from reference: {reference_path}")
        # Use JS to load the reference, create a mask, and inject it
        page.evaluate("""async (refPath) => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => {
                    // Create mask canvas
                    const c = document.createElement('canvas');
                    c.width = img.width;
                    c.height = img.height;
                    const ctx = c.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    const data = ctx.getImageData(0, 0, c.width, c.height);
                    const px = data.data;

                    // Build grayscale mask: bright pixels (near white) = background = black mask
                    // UI pixels = foreground = white mask
                    const maskCanvas = document.createElement('canvas');
                    maskCanvas.width = c.width;
                    maskCanvas.height = c.height;
                    const maskCtx = maskCanvas.getContext('2d');
                    const maskData = maskCtx.createImageData(c.width, c.height);
                    const md = maskData.data;

                    for (let i = 0; i < px.length; i += 4) {
                        const r = px[i], g = px[i+1], b = px[i+2], a = px[i+3];
                        // White or near-white with full alpha = background area
                        const brightness = (r + g + b) / 3;
                        const isBackground = brightness > 240 && a > 200;
                        // Also treat fully transparent as background
                        const isTransparent = a < 30;
                        const isBg = isBackground || isTransparent;
                        const maskVal = isBg ? 0 : 255;
                        md[i] = maskVal;
                        md[i+1] = maskVal;
                        md[i+2] = maskVal;
                        md[i+3] = 255;
                    }
                    maskCtx.putImageData(maskData, 0, 0);

                    // Now inject this as the imported AI mask
                    // We need to set: aiMaskCanvas and importedAiMaskAlpha
                    window._testMaskCanvas = maskCanvas;

                    // Build alpha array from mask
                    const alpha = new Uint8ClampedArray(c.width * c.height);
                    for (let i = 0; i < alpha.length; i++) {
                        alpha[i] = md[i * 4]; // R channel = mask value
                    }
                    window._testMaskAlpha = alpha;
                    resolve({width: c.width, height: c.height, kept: alpha.filter(v => v > 0).length});
                };
                img.onerror = () => reject('Failed to load reference image');
                img.src = refPath;
            });
        }""", f"http://127.0.0.1:8080/input/Quality%20asset.png")
        # We need to serve the reference image - let's copy it to a served location
        # Actually the reference is already at input/Quality asset.png, let's check

    # Inject the mask into the app's global state
    print("Injecting simulated AI mask into app state...")
    result = page.evaluate("""() => {
        if (!window._testMaskCanvas || !window._testMaskAlpha) {
            return {error: 'Mask not created'};
        }
        // Inject into app globals
        aiMaskCanvas = window._testMaskCanvas;
        importedAiMaskAlpha = window._testMaskAlpha;
        return {
            maskWidth: aiMaskCanvas.width,
            maskHeight: aiMaskCanvas.height,
            alphaLen: importedAiMaskAlpha.length,
            nonZero: Array.from(importedAiMaskAlpha).filter(v => v > 0).length
        };
    }""")
    print(f"  Mask injected: {result}")

    # Step 3: Set AI mode with imported mask via JS
    print("Configuring AI mode...")
    page.evaluate("""() => {
        const bgMode = document.querySelector('#bgMode');
        if (bgMode) { bgMode.value = 'ai'; bgMode.dispatchEvent(new Event('change')); }
        const bgMaskSource = document.querySelector('#bgMaskSource');
        if (bgMaskSource) { bgMaskSource.value = 'ai'; bgMaskSource.dispatchEvent(new Event('change')); }
        const bgTone = document.querySelector('#bgTone');
        if (bgTone) { bgTone.value = 'dark'; bgTone.dispatchEvent(new Event('change')); }
    }""")
    page.wait_for_timeout(500)

    page.screenshot(path=os.path.join(output_dir, "ai_01_configured.png"), full_page=True)
    print("AI mode configured.")

    # Step 4: Process
    print("Processing with edge protection + spill cleanup...")
    page.click("#processBgButton")

    try:
        page.wait_for_function(
            """() => {
                const s = document.querySelector('#bgStatus');
                if (!s) return false;
                const t = s.textContent;
                return t.length > 5 && !t.includes('%') && !t.includes('Processing') && !t.includes('Preparing');
            }""",
            timeout=60000
        )
    except Exception as e:
        print(f"  Wait timed out: {e}")
        page.wait_for_timeout(5000)

    page.wait_for_timeout(1000)

    status = page.eval_on_selector("#bgStatus", "el => el.textContent")
    print(f"  Status: {status}")

    page.screenshot(path=os.path.join(output_dir, "ai_02_result.png"), full_page=True)
    print("Result screenshot saved.")

    # Step 5: Also run WITHOUT edge protection for comparison
    # Temporarily disable by clearing the AI mask flag, using remove mode directly
    print("\nRunning comparison WITHOUT edge protection (plain remove mode)...")
    page.select_option("#bgMode", "remove")
    page.select_option("#bgPreset", "ui-balanced")
    page.select_option("#bgTone", "dark")
    page.wait_for_timeout(300)
    page.click("#processBgButton")

    try:
        page.wait_for_function(
            """() => {
                const s = document.querySelector('#bgStatus');
                if (!s) return false;
                const t = s.textContent;
                return t.length > 5 && !t.includes('%') && !t.includes('Processing') && !t.includes('removing');
            }""",
            timeout=60000
        )
    except:
        page.wait_for_timeout(5000)

    page.wait_for_timeout(1000)
    status = page.eval_on_selector("#bgStatus", "el => el.textContent")
    print(f"  Status: {status}")
    page.screenshot(path=os.path.join(output_dir, "ai_03_no_protection_compare.png"), full_page=True)
    print("Comparison screenshot saved.")

    browser.close()
    print("\nAll AI refinement tests complete!")
