"""Download the processed result for closer inspection."""
import sys
import os
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
source_path = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
output_dir = sys.argv[3] if len(sys.argv) > 3 else "test_screenshots"

os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Load source
    if source_path:
        print(f"Loading source: {source_path}")
        with page.expect_file_chooser() as fc_info:
            page.click("#bgInputFile")
        fc_info.value.set_files(source_path)
        page.wait_for_timeout(2000)

    # Inject simulated AI mask from reference
    print("Creating + injecting simulated AI mask...")
    page.evaluate("""async () => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                const c = document.createElement('canvas');
                c.width = img.width;
                c.height = img.height;
                const ctx = c.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const data = ctx.getImageData(0, 0, c.width, c.height);
                const px = data.data;
                const maskCanvas = document.createElement('canvas');
                maskCanvas.width = c.width;
                maskCanvas.height = c.height;
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
                resolve(true);
            };
            img.onerror = () => reject('fail');
            img.src = '/input/Quality%20asset.png';
        });
    }""")

    # Configure AI mode
    page.evaluate("""() => {
        document.querySelector('#bgMode').value = 'ai';
        document.querySelector('#bgMode').dispatchEvent(new Event('change'));
        const ms = document.querySelector('#bgMaskSource');
        if (ms) { ms.value = 'ai'; ms.dispatchEvent(new Event('change')); }
        document.querySelector('#bgTone').value = 'dark';
        document.querySelector('#bgTone').dispatchEvent(new Event('change'));
    }""")
    page.wait_for_timeout(500)

    # Process
    print("Processing...")
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
    print(f"Status: {status}")

    # Extract the result canvas as a data URL and save it
    print("Extracting result image...")
    data_url = page.evaluate("""() => {
        // Get the result canvas from the preview
        const resultCanvas = document.querySelector('#resultCanvas');
        if (resultCanvas) return resultCanvas.toDataURL('image/png');
        // Fallback: try the processed layout canvas
        if (typeof processedLayoutCanvas !== 'undefined' && processedLayoutCanvas) {
            return processedLayoutCanvas.toDataURL('image/png');
        }
        return null;
    }""")

    if data_url:
        import base64
        header, b64data = data_url.split(',', 1)
        raw = base64.b64decode(b64data)
        result_path = os.path.join(output_dir, "ai_result_full.png")
        with open(result_path, 'wb') as f:
            f.write(raw)
        print(f"Result saved: {result_path} ({len(raw)} bytes)")
    else:
        print("Could not extract result canvas")

    # Also get the full-page screenshot with panels expanded
    page.screenshot(path=os.path.join(output_dir, "ai_result_page.png"), full_page=True)

    browser.close()
    print("Done!")
