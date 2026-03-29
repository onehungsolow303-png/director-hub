"""Test background removal presets on a dark multicolor image."""
import sys
import os
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
image_path = sys.argv[2] if len(sys.argv) > 2 else None
output_dir = sys.argv[3] if len(sys.argv) > 3 else "test_screenshots"

os.makedirs(output_dir, exist_ok=True)

PRESETS = ["ui-balanced", "ui-soft", "ui-hard"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Load the test image via file chooser
    if image_path:
        abs_path = os.path.abspath(image_path)
        print(f"Loading image: {abs_path}")
        with page.expect_file_chooser() as fc_info:
            page.click("#bgInputFile")
        file_chooser = fc_info.value
        file_chooser.set_files(abs_path)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(output_dir, "00_loaded.png"), full_page=True)
        print("Image loaded.")

    for preset in PRESETS:
        label = f"{preset}_dark"
        print(f"\nTesting: {label}")

        # Set preset
        page.select_option("#bgPreset", preset)
        page.wait_for_timeout(300)

        # Ensure tone is dark
        page.select_option("#bgTone", "dark")
        page.wait_for_timeout(300)

        # Ensure mode is "remove" (background removal)
        page.select_option("#bgMode", "remove")
        page.wait_for_timeout(300)

        # Click Process Image
        page.click("#processBgButton")

        # Wait for processing - look for status that doesn't contain a percentage
        try:
            page.wait_for_function(
                """() => {
                    const s = document.querySelector('#bgStatus');
                    if (!s) return false;
                    const t = s.textContent;
                    // Processing shows percentages; done shows result text without %
                    return t.length > 5 && !t.includes('%') && !t.includes('Processing') && !t.includes('removing') && (t.includes('Found') || t.includes('panel') || t.includes('Done') || t.includes('complete') || t.includes('Sampled') || t.includes('heuristic') || t.includes('extracted') || t.includes('mask'));
                }""",
                timeout=60000
            )
        except Exception as e:
            print(f"  Wait timed out, capturing anyway: {e}")
            page.wait_for_timeout(3000)

        page.wait_for_timeout(500)

        # Get status text
        status = page.eval_on_selector("#bgStatus", "el => el.textContent")
        print(f"  Status: {status}")

        # Screenshot result
        page.screenshot(path=os.path.join(output_dir, f"{label}_result.png"), full_page=True)
        print(f"  Saved: {label}_result.png")

    # Also test light tone with ui-balanced for comparison
    print("\nTesting: ui-balanced_light")
    page.select_option("#bgPreset", "ui-balanced")
    page.select_option("#bgTone", "light")
    page.select_option("#bgMode", "remove")
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
        page.wait_for_timeout(3000)
    page.wait_for_timeout(500)
    status = page.eval_on_selector("#bgStatus", "el => el.textContent")
    print(f"  Status: {status}")
    page.screenshot(path=os.path.join(output_dir, "ui-balanced_light_result.png"), full_page=True)

    browser.close()
    print("\nAll tests complete!")
