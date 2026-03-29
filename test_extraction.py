"""End-to-end test: load image, process, screenshot result."""
import sys, os, time
from playwright.sync_api import sync_playwright

image_path = os.path.abspath("C:/Dev/Image generator/input/Example UI 1.png")
url = "http://127.0.0.1:8080/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(500)

    # Upload image
    page.set_input_files("#bgInputFile", image_path)
    page.wait_for_timeout(1000)
    page.screenshot(path="test_1_loaded.png", full_page=False)
    print("1. Image loaded")

    # Process with default heuristic mode (Background removal)
    page.click("#processBgButton")
    page.wait_for_timeout(5000)
    page.screenshot(path="test_2_processed.png", full_page=False)
    print("2. Processed with heuristic")

    # Check console for errors
    console_msgs = []
    page.on("console", lambda msg: console_msgs.append(f"{msg.type}: {msg.text}"))

    # Now try AI mask via ComfyUI
    page.click("#comfyuiGenerateMaskButton")
    page.wait_for_timeout(20000)  # Give ComfyUI time
    page.screenshot(path="test_3_aimask.png", full_page=False)
    print("3. After AI mask generation")

    # Process with AI mask
    page.click("#processBgButton")
    page.wait_for_timeout(5000)
    page.screenshot(path="test_4_ai_processed.png", full_page=False)
    print("4. Processed with AI mask")

    for msg in console_msgs:
        if "error" in msg.lower() or "warn" in msg.lower():
            print(f"  CONSOLE: {msg}")

    browser.close()
    print("Done. Check test_*.png files.")
