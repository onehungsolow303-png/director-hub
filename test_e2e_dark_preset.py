"""
End-to-end AI Remove test: dark-balanced preset on cave screenshot.
Uses Playwright to drive the app UI and verify results.
"""
import asyncio
import os
import sys
from pathlib import Path

async def main():
    from playwright.async_api import async_playwright

    test_image = r"C:\Pictures\Screenshots 1\Screenshot 2026-03-27 201511.png"
    app_url = "http://127.0.0.1:8080"
    out_dir = Path(r"C:\Dev\Image generator\test_screenshots")
    out_dir.mkdir(exist_ok=True)

    result_path = out_dir / "e2e_dark_preset_result.png"
    app_screenshot_path = out_dir / "e2e_dark_preset_app.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1000})

        # 1. Open the app
        print("[1] Opening app...")
        await page.goto(app_url, wait_until="networkidle")
        print("    App loaded.")

        # 2. Load the cave screenshot via file chooser
        print("[2] Loading test image via #bgInputFile...")
        file_input = page.locator("#bgInputFile")
        await file_input.set_input_files(test_image)
        # Wait for image to render on canvas
        await page.wait_for_timeout(2000)
        print("    Image loaded.")

        # 3. Verify preset is dark-balanced and tone is dark
        print("[3] Checking preset and tone...")
        preset_val = await page.locator("#bgPreset").input_value()
        tone_val = await page.locator("#bgTone").input_value()
        print(f"    Preset: {preset_val}, Tone: {tone_val}")
        assert preset_val == "dark-balanced", f"Expected dark-balanced, got {preset_val}"
        assert tone_val == "dark", f"Expected dark tone, got {tone_val}"
        print("    Preset/tone verified.")

        # 4. Click AI Remove
        print("[4] Clicking AI Remove...")
        await page.locator("#aiRemoveButton").click()

        # 5. Poll #aiRemoveStatus for "Done" or "failed", up to 60s
        print("[5] Waiting for AI Remove completion (up to 60s)...")
        status_text = ""
        for i in range(120):  # poll every 500ms, up to 60s
            await page.wait_for_timeout(500)
            status_el = page.locator("#aiRemoveStatus")
            is_visible = await status_el.is_visible()
            if is_visible:
                status_text = (await status_el.text_content() or "").strip()
                if "Done" in status_text or "failed" in status_text.lower():
                    break
            if i % 10 == 0:
                print(f"    ...{i*0.5:.0f}s elapsed, status: {status_text[:60]}")
        print(f"    Final status: {status_text}")

        # 6. Check alpha channel stats on #aiFinalCanvas
        print("[6] Analyzing alpha channel on #aiFinalCanvas...")
        alpha_stats = await page.evaluate("""() => {
            const c = document.querySelector('#aiFinalCanvas');
            if (!c || c.width === 0 || c.height === 0) {
                return { error: 'Canvas not found or empty', width: 0, height: 0 };
            }
            const ctx = c.getContext('2d');
            const data = ctx.getImageData(0, 0, c.width, c.height).data;
            const total = c.width * c.height;
            let transparent = 0, semi = 0, opaque = 0;
            for (let i = 3; i < data.length; i += 4) {
                const a = data[i];
                if (a === 0) transparent++;
                else if (a === 255) opaque++;
                else semi++;
            }
            return {
                width: c.width,
                height: c.height,
                total,
                transparent,
                semi,
                opaque,
                pctTransparent: (transparent / total * 100).toFixed(2),
                pctSemi: (semi / total * 100).toFixed(2),
                pctOpaque: (opaque / total * 100).toFixed(2)
            };
        }""")
        print(f"    Canvas: {alpha_stats.get('width')}x{alpha_stats.get('height')}")
        print(f"    Transparent (a=0):   {alpha_stats.get('pctTransparent')}%")
        print(f"    Semi-transparent:    {alpha_stats.get('pctSemi')}%")
        print(f"    Opaque (a=255):      {alpha_stats.get('pctOpaque')}%")

        # 7. Extract result as PNG
        print("[7] Extracting result PNG from canvas...")
        data_url = await page.evaluate("""() => {
            const c = document.querySelector('#aiFinalCanvas');
            return c ? c.toDataURL('image/png') : null;
        }""")
        if data_url:
            import base64
            b64 = data_url.split(",", 1)[1]
            png_bytes = base64.b64decode(b64)
            result_path.write_bytes(png_bytes)
            file_size = result_path.stat().st_size
            print(f"    Saved: {result_path} ({file_size:,} bytes)")
        else:
            file_size = 0
            print("    ERROR: Could not extract canvas data.")

        # 8. Full page screenshot
        print("[8] Taking full page screenshot...")
        await page.screenshot(path=str(app_screenshot_path), full_page=True)
        print(f"    Saved: {app_screenshot_path}")

        await browser.close()

    # 9. Report and pass/fail
    print("\n" + "=" * 60)
    print("E2E DARK-BALANCED PRESET TEST REPORT")
    print("=" * 60)
    print(f"Status text:     {status_text}")
    print(f"Canvas size:     {alpha_stats.get('width')}x{alpha_stats.get('height')}")
    print(f"Alpha stats:")
    print(f"  Transparent:   {alpha_stats.get('pctTransparent')}% ({alpha_stats.get('transparent')} px)")
    print(f"  Semi-transp:   {alpha_stats.get('pctSemi')}% ({alpha_stats.get('semi')} px)")
    print(f"  Opaque:        {alpha_stats.get('pctOpaque')}% ({alpha_stats.get('opaque')} px)")
    print(f"Result file:     {result_path} ({file_size:,} bytes)")
    print(f"App screenshot:  {app_screenshot_path}")

    # Pass/fail checks
    checks = []
    done_ok = "Done" in status_text
    checks.append(("Status shows 'Done'", done_ok))

    pct_trans = float(alpha_stats.get("pctTransparent", 0))
    checks.append((f">=20% transparent (got {pct_trans}%)", pct_trans >= 20))

    pct_opaque = float(alpha_stats.get("pctOpaque", 0))
    checks.append((f">=10% opaque (got {pct_opaque}%)", pct_opaque >= 10))

    checks.append((f"File >100KB (got {file_size:,}B)", file_size > 100_000))

    print("\nPass criteria:")
    all_pass = True
    for label, ok in checks:
        tag = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{tag}] {label}")

    verdict = "PASS" if all_pass else "FAIL"
    print(f"\nOverall: {verdict}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
