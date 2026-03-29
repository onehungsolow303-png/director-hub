"""Debug: check what happens when the mask PNG is loaded into a canvas."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto("http://127.0.0.1:8080/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    # Directly load the mask image and analyze it
    result = page.evaluate("""() => {
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                const c = document.createElement('canvas');
                c.width = img.width;
                c.height = img.height;
                const ctx = c.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const data = ctx.getImageData(0, 0, c.width, c.height).data;

                // Sample first 20 pixels
                let samples = [];
                for (let i = 0; i < 20; i++) {
                    samples.push({r: data[i*4], g: data[i*4+1], b: data[i*4+2], a: data[i*4+3]});
                }

                // Sample from middle
                let midSamples = [];
                const mid = Math.floor(c.width * c.height / 2);
                for (let i = mid; i < mid + 20; i++) {
                    midSamples.push({r: data[i*4], g: data[i*4+1], b: data[i*4+2], a: data[i*4+3]});
                }

                // Sample from bottom (where UI should be)
                let bottomSamples = [];
                const bot = Math.floor(c.width * c.height * 0.9);
                for (let i = bot; i < bot + 20; i++) {
                    bottomSamples.push({r: data[i*4], g: data[i*4+1], b: data[i*4+2], a: data[i*4+3]});
                }

                // Count non-zero
                let nonZeroRGB = 0, nonZeroA = 0;
                const step = Math.max(1, Math.floor(data.length / 4 / 10000));
                for (let i = 0; i < data.length / 4; i += step) {
                    const mx = Math.max(data[i*4], data[i*4+1], data[i*4+2]);
                    if (mx > 0) nonZeroRGB++;
                    if (data[i*4+3] > 0) nonZeroA++;
                }

                // Check alphaFromMaskCanvas detection
                let hasTransparent = false, hasOpaque = false;
                const total = c.width * c.height;
                const detectStep = Math.max(1, Math.floor(total / 20000));
                for (let i = 0; i < total; i += detectStep) {
                    const a = data[i * 4 + 3];
                    if (a < 128) hasTransparent = true;
                    if (a > 128) hasOpaque = true;
                    if (hasTransparent && hasOpaque) break;
                }

                resolve({
                    width: c.width,
                    height: c.height,
                    topPixels: samples,
                    midPixels: midSamples,
                    bottomPixels: bottomSamples,
                    nonZeroRGB_sampled: nonZeroRGB,
                    nonZeroA_sampled: nonZeroA,
                    detection: {hasTransparent, hasOpaque, useAlpha: hasTransparent && hasOpaque}
                });
            };
            img.onerror = () => resolve({error: "Failed to load mask"});
            img.src = "/comfyui/view?filename=_debug_mask_00001_.png&type=output";
        });
    }""")

    print("Direct mask image analysis:")
    if "error" in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Size: {result['width']}x{result['height']}")
        print(f"  Non-zero RGB (sampled): {result['nonZeroRGB_sampled']}")
        print(f"  Non-zero Alpha (sampled): {result['nonZeroA_sampled']}")
        print(f"  Detection: {result['detection']}")
        print(f"  Top pixels (should be 0,0,0 = background): {result['topPixels'][:5]}")
        print(f"  Bottom pixels (should be bright = UI): {result['bottomPixels'][:5]}")

    browser.close()
