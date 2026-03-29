"""Take a screenshot of the app for visual debugging."""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/index.html"
output = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"
click = sys.argv[3] if len(sys.argv) > 3 else None

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(500)
    if click:
        page.click(click)
        page.wait_for_timeout(300)
    page.screenshot(path=output, full_page=True)
    browser.close()
    print(f"Screenshot saved to {output}")
