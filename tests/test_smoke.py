"""Smoke tests — fast sanity checks that the server and app are working.

Run: .venv/Scripts/python.exe -m pytest tests/test_smoke.py -v -m smoke
"""

import urllib.request
import urllib.error

import pytest


APP_URL = "http://127.0.0.1:8080"


@pytest.mark.smoke
class TestServerHealth:
    def test_server_reachable(self):
        """Server at port 8080 should respond to HTTP GET."""
        req = urllib.request.Request(APP_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200

    def test_index_html_served(self):
        """index.html should contain the app title."""
        req = urllib.request.Request(APP_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            assert "Gut It Out" in body or "Asset Editor" in body or "Game UI" in body

    def test_app_js_served(self):
        """app.js should be accessible."""
        req = urllib.request.Request(f"{APP_URL}/app.js")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert len(resp.read()) > 1000


@pytest.mark.smoke
class TestAppLoads:
    def test_page_renders(self, app_ready):
        """App should render without console errors."""
        errors = []
        app_ready.on("pageerror", lambda err: errors.append(str(err)))
        app_ready.wait_for_timeout(1000)
        assert app_ready.locator("#bgInputFile").count() == 1
        assert app_ready.locator("#aiRemoveButton").count() == 1
        assert app_ready.locator("#bgPreset").count() == 1

    def test_canvas_exists(self, app_ready):
        """Result canvas element should exist."""
        assert app_ready.locator("#resultCanvas").count() == 1

    def test_presets_populated(self, app_ready):
        """Preset dropdown should have dark and light options."""
        options = app_ready.locator("#bgPreset option").all_text_contents()
        assert len(options) >= 3
