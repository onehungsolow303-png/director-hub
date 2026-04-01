"""
Debug test: investigate blank AI Enhance output.

RESULT: AI Enhance works correctly in automated testing.
  - processedLayoutCanvas has content (396k opaque + 18k partial-alpha pixels)
  - loadedImage is available with matching dimensions (1376x768)
  - restoreEdgeColorsFromOriginal() produces valid output
  - aiEnhancedCanvas receives the drawn result (1.65M nonzero values)
  - No console errors, no page errors
  - Status text correctly shows "Color restoration complete."

Steps reproduced:
1. Load image, set tone to Light, model to RMBG-2.0
2. Click AI Remove, wait for completion
3. Check aiFinalCanvas has content
4. Click AI Enhance Colors
5. Capture console errors/logs
6. Check aiEnhancedCanvas state
"""
import sys
import os
from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:8080")
IMAGE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "input", "BananaProAI_com-2026320191551.png")
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_screenshots", "enhance_debug")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Collect console messages and page errors
console_messages = []
page_errors = []

def on_console(msg):
    console_messages.append({"type": msg.type, "text": msg.text})

def on_pageerror(err):
    page_errors.append(str(err))


def screenshot(page, name):
    path = os.path.join(OUTPUT_DIR, name)
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def main():
    print(f"Image: {IMAGE_PATH}")
    print(f"Exists: {os.path.isfile(IMAGE_PATH)}")
    print(f"App URL: {APP_URL}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.on("console", on_console)
        page.on("pageerror", on_pageerror)

        # --- Step 1: Load the app ---
        print("Step 1: Loading app...")
        page.goto(APP_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)
        screenshot(page, "01_app_loaded.png")

        # --- Step 2: Load the image ---
        print("Step 2: Loading image...")
        with page.expect_file_chooser() as fc_info:
            page.click("#bgInputFile")
        fc_info.value.set_files(IMAGE_PATH)
        page.wait_for_timeout(2000)
        screenshot(page, "02_image_loaded.png")

        # --- Step 3: Set tone to Light ---
        print("Step 3: Setting tone=light...")
        page.select_option("#bgTone", "light")
        page.wait_for_timeout(500)
        screenshot(page, "03_settings.png")

        # --- Step 4: Click AI Remove and wait ---
        print("Step 4: Clicking AI Remove...")
        console_messages.clear()
        page_errors.clear()

        page.click("#aiRemoveButton")
        # Wait for completion (status text changes to "Done." or error)
        try:
            page.wait_for_function(
                """() => {
                    const s = document.querySelector('#aiRemoveStatus');
                    if (!s) return false;
                    const t = s.textContent;
                    return t.includes('Done') || t.includes('failed') || t.includes('error');
                }""",
                timeout=120000,
            )
        except Exception as e:
            print(f"  WARNING: AI Remove wait timed out: {e}")
        page.wait_for_timeout(1000)
        screenshot(page, "04_ai_remove_done.png")

        ai_remove_status = page.text_content("#aiRemoveStatus")
        print(f"  AI Remove status: {ai_remove_status}")
        if "failed" in (ai_remove_status or "").lower():
            print("  ERROR: AI Remove failed, cannot continue.")
            browser.close()
            return

        # --- Step 5: Check state before clicking Enhance ---
        print("Step 5: Checking pre-enhance state...")

        pre_state = page.evaluate("""() => {
            const aiEnhanceBlock = document.querySelector('#aiEnhanceBlock');
            const aiFinalCanvas = document.querySelector('#aiFinalCanvas');
            const aiEnhancedCanvas = document.querySelector('#aiEnhancedCanvas');
            const aiEnhanceButton = document.querySelector('#aiEnhanceButton');

            // Check processedLayoutCanvas and loadedImage
            const hasProcessedLayout = typeof processedLayoutCanvas !== 'undefined' && processedLayoutCanvas !== null;
            const hasLoadedImage = typeof loadedImage !== 'undefined' && loadedImage !== null;
            const hasImportedAiMaskAlpha = typeof importedAiMaskAlpha !== 'undefined' && importedAiMaskAlpha !== null;

            let processedLayoutDims = null;
            if (hasProcessedLayout) {
                processedLayoutDims = {
                    width: processedLayoutCanvas.width,
                    height: processedLayoutCanvas.height,
                };
                // Check if it has any content
                try {
                    const ctx = processedLayoutCanvas.getContext('2d');
                    const data = ctx.getImageData(0, 0, Math.min(100, processedLayoutCanvas.width), Math.min(100, processedLayoutCanvas.height)).data;
                    let nonZero = 0;
                    for (let i = 0; i < data.length; i++) { if (data[i] !== 0) nonZero++; }
                    processedLayoutDims.nonZeroPixelValues = nonZero;
                    processedLayoutDims.totalValues = data.length;
                } catch(e) {
                    processedLayoutDims.error = e.message;
                }
            }

            let loadedImageDims = null;
            if (hasLoadedImage) {
                loadedImageDims = {
                    width: loadedImage.width || loadedImage.naturalWidth,
                    height: loadedImage.height || loadedImage.naturalHeight,
                    complete: loadedImage.complete,
                    tagName: loadedImage.tagName,
                };
            }

            return {
                enhanceBlockDisplay: aiEnhanceBlock ? aiEnhanceBlock.style.display : 'NOT FOUND',
                enhanceButtonExists: !!aiEnhanceButton,
                enhanceButtonDisabled: aiEnhanceButton ? aiEnhanceButton.disabled : null,
                finalCanvasExists: !!aiFinalCanvas,
                finalCanvasDims: aiFinalCanvas ? { w: aiFinalCanvas.width, h: aiFinalCanvas.height } : null,
                enhancedCanvasExists: !!aiEnhancedCanvas,
                enhancedCanvasDims: aiEnhancedCanvas ? { w: aiEnhancedCanvas.width, h: aiEnhancedCanvas.height } : null,
                hasProcessedLayout,
                processedLayoutDims,
                hasLoadedImage,
                loadedImageDims,
                hasImportedAiMaskAlpha,
            };
        }""")

        print(f"  Enhance block display: {pre_state['enhanceBlockDisplay']}")
        print(f"  Enhance button exists: {pre_state['enhanceButtonExists']}, disabled: {pre_state['enhanceButtonDisabled']}")
        print(f"  aiFinalCanvas: exists={pre_state['finalCanvasExists']}, dims={pre_state['finalCanvasDims']}")
        print(f"  aiEnhancedCanvas: exists={pre_state['enhancedCanvasExists']}, dims={pre_state['enhancedCanvasDims']}")
        print(f"  processedLayoutCanvas: present={pre_state['hasProcessedLayout']}, dims={pre_state.get('processedLayoutDims')}")
        print(f"  loadedImage: present={pre_state['hasLoadedImage']}, info={pre_state.get('loadedImageDims')}")
        print(f"  importedAiMaskAlpha: present={pre_state['hasImportedAiMaskAlpha']}")

        # Check aiFinalCanvas has content
        final_has_content = page.evaluate("""() => {
            const c = document.querySelector('#aiFinalCanvas');
            if (!c || c.width < 2 || c.height < 2) return { hasContent: false, reason: 'canvas too small or missing' };
            const ctx = c.getContext('2d');
            const data = ctx.getImageData(0, 0, c.width, c.height).data;
            let nonZero = 0;
            for (let i = 0; i < data.length; i++) { if (data[i] !== 0) nonZero++; }
            return { hasContent: nonZero > 0, nonZeroValues: nonZero, totalValues: data.length, width: c.width, height: c.height };
        }""")
        print(f"  aiFinalCanvas content check: {final_has_content}")

        # --- Step 6: Click AI Enhance Colors ---
        print("Step 6: Clicking AI Enhance Colors...")
        console_messages.clear()
        page_errors.clear()

        # Scroll to the button first
        page.evaluate("document.querySelector('#aiEnhanceButton').scrollIntoView()")
        page.wait_for_timeout(300)

        page.click("#aiEnhanceButton")
        page.wait_for_timeout(2000)  # Give it time to process
        screenshot(page, "05_after_enhance.png")

        # --- Step 7: Check post-enhance state ---
        print("Step 7: Checking post-enhance state...")

        enhance_status = page.text_content("#aiEnhanceStatus")
        print(f"  Enhance status text: {enhance_status}")

        post_state = page.evaluate("""() => {
            const aiEnhancedCanvas = document.querySelector('#aiEnhancedCanvas');
            const dims = aiEnhancedCanvas ? { w: aiEnhancedCanvas.width, h: aiEnhancedCanvas.height } : null;

            let hasContent = false;
            let nonZero = 0;
            let totalValues = 0;
            if (aiEnhancedCanvas && aiEnhancedCanvas.width > 1 && aiEnhancedCanvas.height > 1) {
                const ctx = aiEnhancedCanvas.getContext('2d');
                const data = ctx.getImageData(0, 0, aiEnhancedCanvas.width, aiEnhancedCanvas.height).data;
                totalValues = data.length;
                for (let i = 0; i < data.length; i++) { if (data[i] !== 0) nonZero++; }
                hasContent = nonZero > 0;
            }

            // Also check lastEnhancedCanvas
            const hasLastEnhanced = typeof lastEnhancedCanvas !== 'undefined' && lastEnhancedCanvas !== null;
            let lastEnhancedInfo = null;
            if (hasLastEnhanced) {
                lastEnhancedInfo = { w: lastEnhancedCanvas.width, h: lastEnhancedCanvas.height };
                const ctx2 = lastEnhancedCanvas.getContext('2d');
                const d2 = ctx2.getImageData(0, 0, lastEnhancedCanvas.width, lastEnhancedCanvas.height).data;
                let nz = 0;
                for (let i = 0; i < d2.length; i++) { if (d2[i] !== 0) nz++; }
                lastEnhancedInfo.nonZero = nz;
                lastEnhancedInfo.total = d2.length;
            }

            return {
                enhancedDims: dims,
                hasContent,
                nonZero,
                totalValues,
                hasLastEnhanced,
                lastEnhancedInfo,
            };
        }""")

        print(f"  aiEnhancedCanvas dims: {post_state['enhancedDims']}")
        print(f"  aiEnhancedCanvas has content: {post_state['hasContent']} (nonZero={post_state['nonZero']}/{post_state['totalValues']})")
        print(f"  lastEnhancedCanvas: present={post_state['hasLastEnhanced']}, info={post_state.get('lastEnhancedInfo')}")

        # --- Step 8: Report console messages and errors ---
        print()
        print("=== Console messages during AI Enhance ===")
        for msg in console_messages:
            print(f"  [{msg['type']}] {msg['text']}")
        if not console_messages:
            print("  (none)")

        print()
        print("=== Page errors during AI Enhance ===")
        for err in page_errors:
            print(f"  ERROR: {err}")
        if not page_errors:
            print("  (none)")

        # --- Step 9: Deep dive - test restoreEdgeColorsFromOriginal directly ---
        print()
        print("Step 9: Direct function call diagnostics...")

        diag = page.evaluate("""() => {
            const result = {};

            // Check processedLayoutCanvas pixel data
            if (typeof processedLayoutCanvas !== 'undefined' && processedLayoutCanvas) {
                const ctx = processedLayoutCanvas.getContext('2d');
                const w = processedLayoutCanvas.width;
                const h = processedLayoutCanvas.height;
                const data = ctx.getImageData(0, 0, w, h).data;
                let alphaZero = 0, alphaFull = 0, alphaPartial = 0;
                for (let i = 3; i < data.length; i += 4) {
                    if (data[i] === 0) alphaZero++;
                    else if (data[i] === 255) alphaFull++;
                    else alphaPartial++;
                }
                result.processedLayout = {
                    width: w, height: h,
                    totalPixels: w * h,
                    alphaZero, alphaFull, alphaPartial,
                };
            } else {
                result.processedLayout = null;
            }

            // Check loadedImage availability
            if (typeof loadedImage !== 'undefined' && loadedImage) {
                result.loadedImage = {
                    tagName: loadedImage.tagName,
                    width: loadedImage.width || loadedImage.naturalWidth,
                    height: loadedImage.height || loadedImage.naturalHeight,
                    complete: loadedImage.complete,
                };
                // Try creating source canvas from it
                try {
                    const sc = document.createElement('canvas');
                    sc.width = loadedImage.width || loadedImage.naturalWidth;
                    sc.height = loadedImage.height || loadedImage.naturalHeight;
                    sc.getContext('2d').drawImage(loadedImage, 0, 0);
                    const sd = sc.getContext('2d').getImageData(0, 0, Math.min(50, sc.width), Math.min(50, sc.height)).data;
                    let nz = 0;
                    for (let i = 0; i < sd.length; i++) { if (sd[i] !== 0) nz++; }
                    result.sourceCanvasFromLoadedImage = { width: sc.width, height: sc.height, nonZero: nz };
                } catch(e) {
                    result.sourceCanvasFromLoadedImage = { error: e.message };
                }
            } else {
                result.loadedImage = null;
            }

            // Check dimension mismatch
            if (result.processedLayout && result.loadedImage) {
                result.dimensionMatch = (
                    result.processedLayout.width === result.loadedImage.width &&
                    result.processedLayout.height === result.loadedImage.height
                );
            }

            // Try calling restoreEdgeColorsFromOriginal manually
            try {
                if (typeof processedLayoutCanvas !== 'undefined' && processedLayoutCanvas &&
                    typeof loadedImage !== 'undefined' && loadedImage) {
                    const sourceCanvas = document.createElement('canvas');
                    sourceCanvas.width = loadedImage.width || loadedImage.naturalWidth;
                    sourceCanvas.height = loadedImage.height || loadedImage.naturalHeight;
                    sourceCanvas.getContext('2d').drawImage(loadedImage, 0, 0);

                    const enhanced = restoreEdgeColorsFromOriginal(processedLayoutCanvas, sourceCanvas);
                    const ectx = enhanced.getContext('2d');
                    const edata = ectx.getImageData(0, 0, enhanced.width, enhanced.height).data;
                    let nz = 0;
                    for (let i = 0; i < edata.length; i++) { if (edata[i] !== 0) nz++; }
                    result.manualEnhanceTest = {
                        width: enhanced.width,
                        height: enhanced.height,
                        nonZero: nz,
                        totalValues: edata.length,
                    };
                } else {
                    result.manualEnhanceTest = { error: 'missing inputs' };
                }
            } catch(e) {
                result.manualEnhanceTest = { error: e.message, stack: e.stack ? e.stack.substring(0, 500) : '' };
            }

            return result;
        }""")

        print(f"  processedLayoutCanvas: {diag.get('processedLayout')}")
        print(f"  loadedImage: {diag.get('loadedImage')}")
        print(f"  sourceCanvas from loadedImage: {diag.get('sourceCanvasFromLoadedImage')}")
        print(f"  Dimension match: {diag.get('dimensionMatch')}")
        print(f"  Manual enhance test: {diag.get('manualEnhanceTest')}")

        # Summary
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if pre_state['enhanceBlockDisplay'] == 'none':
            print("FINDING: AI Enhance block is hidden (display:none).")
            print("  -> showAiEnhanceBlock() was never called or failed.")
            print("  -> Check: settings.mode==='ai' && importedAiMaskAlpha")

        if not pre_state['hasProcessedLayout']:
            print("FINDING: processedLayoutCanvas is null/undefined.")

        if not pre_state['hasLoadedImage']:
            print("FINDING: loadedImage is null/undefined.")

        if post_state['enhancedDims'] and post_state['enhancedDims']['w'] <= 1:
            print("FINDING: aiEnhancedCanvas still has width=1 after Enhance.")
            print("  -> runAiEnhance() likely bailed out early or threw an error.")

        if not post_state['hasContent'] and post_state['enhancedDims'] and post_state['enhancedDims']['w'] > 1:
            print("FINDING: aiEnhancedCanvas has correct dimensions but zero content.")
            print("  -> restoreEdgeColorsFromOriginal returned empty canvas.")

        if diag.get('dimensionMatch') is False:
            print(f"FINDING: DIMENSION MISMATCH between processedLayoutCanvas and loadedImage!")
            print(f"  -> processedLayout: {diag['processedLayout']['width']}x{diag['processedLayout']['height']}")
            print(f"  -> loadedImage: {diag['loadedImage']['width']}x{diag['loadedImage']['height']}")
            print("  -> This causes getImageData to read mismatched regions.")

        if diag.get('processedLayout') and diag['processedLayout']['alphaPartial'] == 0:
            print("FINDING: processedLayoutCanvas has ZERO partial-alpha pixels.")
            print(f"  -> alphaZero={diag['processedLayout']['alphaZero']}, alphaFull={diag['processedLayout']['alphaFull']}, alphaPartial={diag['processedLayout']['alphaPartial']}")
            print("  -> restoreEdgeColorsFromOriginal only restores edges on partial-alpha pixels.")
            print("  -> All pixels are either fully opaque or fully transparent, so no blending occurs.")

        manual_test = diag.get('manualEnhanceTest', {})
        if manual_test.get('error'):
            print(f"FINDING: Manual enhance test threw error: {manual_test['error']}")
            if manual_test.get('stack'):
                print(f"  Stack: {manual_test['stack']}")
        elif manual_test.get('nonZero', -1) == 0:
            print("FINDING: Manual enhance test returned all-zero canvas.")
            print("  -> The restoreEdgeColorsFromOriginal function produces empty output.")
        elif manual_test.get('nonZero', 0) > 0:
            print(f"FINDING: Manual enhance test DID produce content (nonZero={manual_test['nonZero']}).")
            print("  -> The function works when called directly; issue is in runAiEnhance() or canvas drawing.")

        browser.close()

    print()
    print("Done. Screenshots saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
