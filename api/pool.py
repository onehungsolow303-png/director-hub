# api/pool.py
"""Playwright session pool — manages headless browser workers."""
import queue
import threading
from playwright.sync_api import sync_playwright


class PlaywrightPool:
    def __init__(self, app_url, size=2):
        self._app_url = app_url
        self._size = size
        self._pool = queue.Queue(maxsize=size)
        self._playwright = None
        self._browser = None
        self._pages = []
        self._lock = threading.Lock()
        self._started = False

    def start(self):
        with self._lock:
            if self._started:
                return
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            for _ in range(self._size):
                context = self._browser.new_context(viewport={"width": 1600, "height": 1200})
                page = context.new_page()
                page.goto(self._app_url, wait_until="networkidle")
                page.wait_for_timeout(1000)
                self._pages.append(page)
                self._pool.put(page)
            self._started = True

    def checkout(self, timeout=30):
        try:
            return self._pool.get(timeout=timeout)
        except queue.Empty:
            return None

    def checkin(self, page):
        self._pool.put(page)

    def reset_page(self, page):
        page.goto(self._app_url, wait_until="networkidle")
        page.wait_for_timeout(500)

    def stop(self):
        with self._lock:
            if not self._started:
                return
            for page in self._pages:
                try:
                    page.context.close()
                except Exception:
                    pass
            self._pages.clear()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            self._started = False

    @property
    def available(self):
        return self._pool.qsize()

    @property
    def total(self):
        return self._size
