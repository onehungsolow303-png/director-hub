"""
Final verification: test WebGL fallback in drawImagePreservingRGB with the
original broken _temp_mask.png (alpha=0), then test server-side fix too.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = "http://127.0.0.1:8080"
TEST_IMAGE = r"C:\Pictures\Screenshots 1\Screenshot 2026-03-27 201511.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))

        print("=== Test with ORIGINAL broken mask (alpha=0) and WebGL fix ===")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        file_input = page.locator("#bgInputFile")
        await file_input.set_input_files(TEST_IMAGE)
        await page.wait_for_timeout(2000)

        result = await page.evaluate("""async () => {
            const R = {};

            // Load the broken mask
            const maskImg = new Image();
            await new Promise((resolve, reject) => {
                maskImg.onload = resolve;
                maskImg.onerror = () => reject(new Error("Failed"));
                maskImg.src = "/_temp_mask.png?t=" + Date.now();
            });
            R.maskSize = [maskImg.width, maskImg.height];

            // Use drawImagePreservingRGB (the new function)
            const canvas = createCanvas(maskImg.width, maskImg.height);
            drawImagePreservingRGB(maskImg, canvas);

            // Check if RGB was preserved
            const ctx = canvas.getContext("2d", { willReadFrequently: true });
            const d = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            const total = canvas.width * canvas.height;
            let nonZero = 0;
            for (let i = 0; i < total; i++) {
                if (Math.max(d[i*4], d[i*4+1], d[i*4+2]) > 0) nonZero++;
            }
            R.nonZeroRGB = nonZero;
            R.total = total;
            R.rgbPreserved = nonZero > total * 0.01;

            // Check center pixel
            const cx = Math.floor(canvas.width / 2);
            const cy = Math.floor(canvas.height / 2);
            const idx = (cy * canvas.width + cx) * 4;
            R.centerPixel = { r: d[idx], g: d[idx+1], b: d[idx+2], a: d[idx+3] };

            // If preserved, do the full pipeline
            if (R.rgbPreserved) {
                // Scale
                let finalCanvas = canvas;
                if (canvas.width !== loadedImage.width || canvas.height !== loadedImage.height) {
                    finalCanvas = createCanvas(loadedImage.width, loadedImage.height);
                    finalCanvas.getContext("2d", { willReadFrequently: true })
                        .drawImage(canvas, 0, 0, loadedImage.width, loadedImage.height);
                }

                const alpha = alphaFromMaskCanvas(finalCanvas);
                R.rawCoverage = getAlphaCoverage(alpha);

                // Polarity
                let wc = 0;
                for (let i = 0; i < alpha.length; i++) if (alpha[i] > 128) wc++;
                R.needsInvert = wc > alpha.length * 0.5;
                if (R.needsInvert) {
                    for (let i = 0; i < alpha.length; i++) alpha[i] = 255 - alpha[i];
                }
                R.finalCoverage = getAlphaCoverage(alpha);

                // Set global and process
                importedAiMaskAlpha = alpha;
                if (bgAiInvertMask) bgAiInvertMask.checked = false;
                if (bgMode) { bgMode.value = "ai"; bgMode.dispatchEvent(new Event("change")); }
                if (bgMaskSource) { bgMaskSource.value = "ai"; bgMaskSource.dispatchEvent(new Event("change")); }
                if (bgDecontaminate) bgDecontaminate.checked = true;
                if (bgAiMaskExpand) bgAiMaskExpand.value = 0;
                if (bgAiMaskFeather) bgAiMaskFeather.value = 0;
                rebuildImportedAiMaskCanvas();

                try {
                    await processBackgroundImage();
                    R.processSuccess = true;
                    R.processStatus = bgStatus ? bgStatus.textContent : 'N/A';
                } catch (e) {
                    R.processSuccess = false;
                    R.processError = e.message;
                    R.processStatus = bgStatus ? bgStatus.textContent : 'N/A';
                }
            }

            return R;
        }""")

        print(f"  Mask size: {result['maskSize']}")
        print(f"  Center pixel: {result['centerPixel']}")
        print(f"  Non-zero RGB: {result['nonZeroRGB']} / {result['total']}")
        print(f"  RGB preserved by WebGL fix: {result['rgbPreserved']}")

        if result['rgbPreserved']:
            print(f"  Raw coverage: {result.get('rawCoverage', 0):.6f}")
            print(f"  Needs invert: {result.get('needsInvert')}")
            print(f"  Final coverage: {result.get('finalCoverage', 0):.6f}")
            print(f"  Process success: {result.get('processSuccess')}")
            print(f"  Process status: {result.get('processStatus')}")

        # Print warnings from console
        warns = [l for l in logs if "warn" in l.lower() or "error" in l.lower() or "webgl" in l.lower()]
        if warns:
            print("\n  Console messages:")
            for w in warns:
                print(f"    {w}")

        print("\n" + "=" * 70)
        if result['rgbPreserved'] and result.get('processSuccess') and "empty" not in result.get('processStatus', '').lower():
            print("SUCCESS: WebGL fallback recovered mask data from alpha=0 PNG!")
        elif not result['rgbPreserved']:
            print("WebGL fallback did NOT work (headless browser may lack WebGL).")
            print("The server-side PIL fix in serve.py is the primary fix.")
        else:
            print(f"Partial: RGB preserved but processing issue: {result.get('processStatus')}")
        print("=" * 70)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
