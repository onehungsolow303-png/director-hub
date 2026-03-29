"""End-to-end test: light-balanced preset on a white-background UI sheet."""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1000})
        await page.goto("http://127.0.0.1:8080", wait_until="networkidle")
        print("[1] Page loaded")

        # 2. Open Advanced Settings card
        await page.evaluate('() => document.querySelector(".card.closed")?.classList.remove("closed")')
        await page.wait_for_timeout(300)
        print("[2] Advanced Settings opened")

        # 3. Load UI sheet image via file chooser
        file_input = page.locator("#bgInputFile")
        await file_input.set_input_files(r"C:\Dev\Image generator\input\UI2.1.png")
        await page.wait_for_timeout(1000)
        print("[3] Image loaded")

        # 4. Select light-balanced preset
        await page.select_option("#bgPreset", "light-balanced")
        await page.wait_for_timeout(500)
        print("[4] Light-balanced preset selected")

        # 5. Read back all preset settings
        threshold = await page.eval_on_selector("#bgThreshold", "el => el.value")
        softness = await page.eval_on_selector("#bgSoftness", "el => el.value")
        tone = await page.eval_on_selector("#bgTone", "el => el.value")
        strong_border = await page.eval_on_selector("#bgStrongBorderRepair", "el => el.checked")
        preserve_color = await page.eval_on_selector("#bgPreserveColor", "el => el.checked")
        edge_cleanup = await page.eval_on_selector("#bgEdgeCleanupStrength", "el => el.value")
        model = await page.eval_on_selector("#comfyuiModel", "el => el.value")

        print(f"[5] Preset settings:")
        print(f"    threshold      = {threshold}  (expected 12)")
        print(f"    softness       = {softness}  (expected 20)")
        print(f"    tone           = {tone}  (expected light)")
        print(f"    strongBorder   = {strong_border}  (expected True)")
        print(f"    preserveColor  = {preserve_color}  (expected True)")
        print(f"    edgeCleanup    = {edge_cleanup}  (expected 55)")
        print(f"    model          = {model}  (expected RMBG-2.0)")

        # 6. Verify tone and model
        tone_ok = tone == "light"
        model_ok = model == "RMBG-2.0"
        settings_pass = (
            str(threshold) == "12"
            and str(softness) == "20"
            and tone_ok
            and strong_border is True
            and preserve_color is True
            and str(edge_cleanup) == "55"
            and model_ok
        )
        print(f"[6] Tone=light: {tone_ok}, Model=RMBG-2.0: {model_ok}, All settings correct: {settings_pass}")

        # 7. Click Process Image
        await page.click("#processBgButton")
        print("[7] Process Image clicked")

        # 8. Wait for completion (poll up to 30s)
        status_text = ""
        for i in range(60):
            await page.wait_for_timeout(500)
            status_text = await page.eval_on_selector("#bgStatus", "el => el.textContent")
            status_text = status_text.strip()
            if status_text and "Processing" not in status_text and "%" not in status_text:
                break
        print(f"[8] Status text: {status_text}")

        # 9. Check if result preview has content
        has_result = await page.evaluate("""() => {
            const canvas = document.querySelector('#resultCanvas');
            if (!canvas) return false;
            if (canvas.width === 0 || canvas.height === 0) return false;
            const ctx = canvas.getContext('2d');
            const data = ctx.getImageData(0, 0, Math.min(canvas.width, 10), Math.min(canvas.height, 10)).data;
            return data.some(v => v !== 0);
        }""")
        print(f"[9] Result preview has content: {has_result}")

        # 10. Screenshot
        await page.screenshot(path=r"C:\Dev\Image generator\test_screenshots\e2e_light_preset_app.png", full_page=True)
        print("[10] Screenshot saved")

        # Final verdict
        overall = settings_pass and has_result and ("Processing" not in status_text)
        print(f"\n{'='*50}")
        print(f"RESULT: {'PASS' if overall else 'FAIL'}")
        if not settings_pass:
            print("  - Preset settings mismatch")
        if not has_result:
            print("  - No result in preview canvas")
        if "Processing" in status_text:
            print("  - Processing did not complete")
        print(f"{'='*50}")

        await browser.close()

asyncio.run(main())
