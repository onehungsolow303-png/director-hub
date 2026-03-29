"""Capture ALL console output during mask generation."""
from playwright.sync_api import sync_playwright
import os

console_msgs = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.on("console", lambda msg: console_msgs.append(msg.text))
    page.on("pageerror", lambda err: console_msgs.append(f"PAGE ERROR: {err.message}"))

    page.goto("http://127.0.0.1:8080/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.set_input_files("#bgInputFile", os.path.abspath("C:/Dev/Image generator/input/Example UI 1.png"))
    page.wait_for_timeout(1000)

    page.click("#comfyuiGenerateMaskButton")
    page.wait_for_timeout(25000)

    print(f"Total console messages: {len(console_msgs)}")
    for msg in console_msgs:
        print(f"  {msg[:200]}")

    browser.close()
