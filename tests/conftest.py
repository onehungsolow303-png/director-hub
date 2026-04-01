"""pytest fixtures for the unified live test system.

Provides:
- browser: Session-scoped Chromium instance
- page: Function-scoped page with fresh context
- app_ready: Page navigated to app and ready for interaction
- golden_images: Session-scoped dict of reference PIL Images
- output_dir: Per-test output directory for screenshots/canvases
"""

import json
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

from helpers.server_manager import ensure_services

ROOT = Path(r"C:\Dev\Image generator")
APP_URL = "http://127.0.0.1:8080"
GOLDEN_DIR = ROOT / "tests" / "golden"
REPORTS_DIR = ROOT / "tests" / "reports"


@pytest.fixture(scope="session", autouse=True)
def ensure_services_ready():
    """Auto-start serve.py before any test that needs it.

    Runs once per session. Detects already-running service and
    restarts serve.py if source files changed since it started.
    """
    _unused, serve_ok = ensure_services()
    yield None, serve_ok


@pytest.fixture(scope="session")
def playwright_instance():
    """Session-scoped Playwright instance."""
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Session-scoped headless Chromium browser."""
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--disable-gpu"],
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Function-scoped page with fresh browser context."""
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def app_ready(page):
    """Page navigated to the app and ready for interaction."""
    page.goto(APP_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    return page


@pytest.fixture(scope="session")
def golden_images():
    """Session-scoped dict of all golden reference images."""
    images = {}
    for path in GOLDEN_DIR.glob("*.png"):
        key = path.stem
        images[key] = Image.open(path).convert("RGBA")
    for path in GOLDEN_DIR.glob("*.PNG"):
        key = path.stem
        if key not in images:
            images[key] = Image.open(path).convert("RGBA")
    return images


@pytest.fixture(scope="function")
def output_dir(request):
    """Per-test output directory for screenshots and extracted canvases."""
    test_name = request.node.name.replace("[", "_").replace("]", "").replace("-", "_")
    out = REPORTS_DIR / "diffs" / test_name
    out.mkdir(parents=True, exist_ok=True)
    return out


@pytest.fixture(scope="session")
def dark_source_path():
    return str(GOLDEN_DIR / "dark_source.png")


@pytest.fixture(scope="session")
def light_source_path():
    return str(GOLDEN_DIR / "light_source.png")


# ── Production test fixtures ──

PROD_DARK_SOURCE = ROOT / "input" / "Example quality image extraction" / "Dark background examples" / "Original Image dark background.png"
PROD_DARK_REF = ROOT / "input" / "Example quality image extraction" / "Dark background examples" / "example preview ectraction dark background removed.PNG"
PROD_LIGHT_SOURCE = ROOT / "input" / "Example quality image extraction" / "Light background examples" / "Original Image White background.png"
PROD_LIGHT_REF = ROOT / "input" / "Example quality image extraction" / "Light background examples" / "example preview ectraction white background removed.PNG"
PROD_ITERATIONS_PATH = REPORTS_DIR / "production_iterations.json"


@pytest.fixture(scope="session")
def prod_dark_source():
    return str(PROD_DARK_SOURCE)


@pytest.fixture(scope="session")
def prod_dark_ref():
    return Image.open(PROD_DARK_REF).convert("RGBA")


@pytest.fixture(scope="session")
def prod_light_source():
    return str(PROD_LIGHT_SOURCE)


@pytest.fixture(scope="session")
def prod_light_ref():
    return Image.open(PROD_LIGHT_REF).convert("RGBA")


@pytest.fixture(scope="session")
def prod_tier():
    """Read current quality tier from production iterations state file."""
    if PROD_ITERATIONS_PATH.exists():
        with open(PROD_ITERATIONS_PATH) as f:
            state = json.load(f)
        return state.get("current_tier", 1)
    return 1
