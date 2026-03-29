"""Test the full AI Remove → Process → Enhance workflow."""
import sys
import os
import base64
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
source_path = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
output_dir = sys.argv[3] if len(sys.argv) > 3 else "test_screenshots"

os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1200})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Step 1: Load source
    if source_path:
        print(f"1. Loading source: {source_path}")
        with page.expect_file_chooser() as fc_info:
            page.click("#bgInputFile")
        fc_info.value.set_files(source_path)
        page.wait_for_timeout(2000)

    # Step 2: Select dark tone (already default)
    print("2. Setting Dark (multicolor) tone")
    page.select_option("#bgTone", "dark")
    page.wait_for_timeout(300)

    # Simulate step 3 (AI Remove) by injecting mock mask + configuring
    print("3. Simulating AI Remove (injecting mock mask)...")
    page.evaluate("""async () => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                const c = document.createElement('canvas');
                c.width = img.width; c.height = img.height;
                const ctx = c.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const data = ctx.getImageData(0, 0, c.width, c.height);
                const px = data.data;
                const maskCanvas = document.createElement('canvas');
                maskCanvas.width = c.width; maskCanvas.height = c.height;
                const maskCtx = maskCanvas.getContext('2d');
                const maskData = maskCtx.createImageData(c.width, c.height);
                const md = maskData.data;
                for (let i = 0; i < px.length; i += 4) {
                    const brightness = (px[i] + px[i+1] + px[i+2]) / 3;
                    const isBg = (brightness > 240 && px[i+3] > 200) || px[i+3] < 30;
                    const v = isBg ? 0 : 255;
                    md[i] = v; md[i+1] = v; md[i+2] = v; md[i+3] = 255;
                }
                maskCtx.putImageData(maskData, 0, 0);
                aiMaskCanvas = maskCanvas;
                const alpha = new Uint8ClampedArray(c.width * c.height);
                for (let i = 0; i < alpha.length; i++) alpha[i] = md[i * 4];
                importedAiMaskAlpha = alpha;
                // Set AI mode + imported mask
                document.querySelector('#bgMode').value = 'ai';
                document.querySelector('#bgMode').dispatchEvent(new Event('change'));
                const ms = document.querySelector('#bgMaskSource');
                if (ms) { ms.value = 'ai'; ms.dispatchEvent(new Event('change')); }
                document.querySelector('#bgDecontaminate').checked = true;
                resolve(true);
            };
            img.onerror = () => reject('fail');
            img.src = '/input/Quality%20asset.png';
        });
    }""")
    page.wait_for_timeout(500)

    # Step 4: Process Image
    print("4. Processing image...")
    page.click("#processBgButton")
    try:
        page.wait_for_function("""() => {
            const s = document.querySelector('#bgStatus');
            return s && s.textContent.length > 5 && !s.textContent.includes('%') && !s.textContent.includes('Preparing');
        }""", timeout=60000)
    except:
        page.wait_for_timeout(5000)
    page.wait_for_timeout(1000)

    status = page.eval_on_selector("#bgStatus", "el => el.textContent")
    print(f"   Status: {status}")

    # Check if AI Enhance block is visible
    enhance_visible = page.evaluate("() => document.querySelector('#aiEnhanceBlock').style.display !== 'none'")
    print(f"   AI Enhance block visible: {enhance_visible}")

    page.screenshot(path=os.path.join(output_dir, "workflow_04_processed.png"), full_page=True)

    # Step 5: AI Enhance
    print("5. Running AI Enhance...")
    page.click("#aiEnhanceButton")
    page.wait_for_timeout(1000)

    enhance_status = page.eval_on_selector("#aiEnhanceStatus", "el => el.textContent")
    print(f"   Enhance status: {enhance_status}")

    page.screenshot(path=os.path.join(output_dir, "workflow_05_enhanced.png"), full_page=True)

    # Extract both canvases
    for canvas_id, name in [("aiFinalCanvas", "final"), ("aiEnhancedCanvas", "enhanced")]:
        data_url = page.evaluate(f"""() => {{
            const c = document.querySelector('#{canvas_id}');
            return c && c.width > 1 ? c.toDataURL('image/png') : null;
        }}""")
        if data_url:
            raw = base64.b64decode(data_url.split(',', 1)[1])
            path = os.path.join(output_dir, f"workflow_{name}.png")
            with open(path, 'wb') as f:
                f.write(raw)
            print(f"   Saved {name}: {path} ({len(raw)} bytes)")

    browser.close()
    print("\nFull workflow test complete!")
