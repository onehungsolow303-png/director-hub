# api/pool.py
"""Playwright session pool — manages headless browser workers.

Playwright sync API requires all page operations to happen on the thread
that created the playwright instance. This pool runs a dedicated worker
thread that owns all pages. External threads submit callables via
run_on_page(), which executes them on the pool thread and returns results.
"""
import queue
import threading
import traceback
from playwright.sync_api import sync_playwright


class _WorkItem:
    """A callable + result future for cross-thread execution."""
    __slots__ = ("fn", "result", "error", "done")

    def __init__(self, fn):
        self.fn = fn
        self.result = None
        self.error = None
        self.done = threading.Event()


class PlaywrightPool:
    def __init__(self, app_url, size=2):
        self._app_url = app_url
        self._size = size
        self._playwright = None
        self._browser = None
        self._pages = []
        self._page_pool = queue.Queue(maxsize=size)
        self._work_queue = queue.Queue()
        self._thread = None
        self._started = False
        self._stop_event = threading.Event()

    def start(self):
        """Start the pool thread. Blocks until pages are ready."""
        if self._started:
            return
        ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(ready,), daemon=True)
        self._thread.start()
        ready.wait(timeout=120)
        self._started = True

    def _run(self, ready_event):
        """Pool thread main loop — owns Playwright and processes work items."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        for _ in range(self._size):
            context = self._browser.new_context(viewport={"width": 1600, "height": 1200})
            page = context.new_page()
            page.goto(self._app_url, wait_until="networkidle")
            page.wait_for_timeout(1000)
            self._pages.append(page)
            self._page_pool.put(page)
        ready_event.set()

        # Process work items until stopped
        while not self._stop_event.is_set():
            try:
                item = self._work_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:  # poison pill
                break
            try:
                item.result = item.fn(self)
            except Exception as e:
                item.error = e
                traceback.print_exc()
            finally:
                item.done.set()

        # Cleanup
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

    def run_on_page(self, fn, timeout=120):
        """Execute fn(pool) on the pool thread. fn should call checkout/checkin.

        Args:
            fn: callable(pool) -> result. Runs on the pool thread.
            timeout: seconds to wait for completion.

        Returns:
            Whatever fn returns.

        Raises:
            TimeoutError if fn doesn't complete in time.
            Any exception fn raises.
        """
        if not self._started:
            raise RuntimeError("Pool not started")
        item = _WorkItem(fn)
        self._work_queue.put(item)
        if not item.done.wait(timeout=timeout):
            raise TimeoutError(f"Pool operation timed out after {timeout}s")
        if item.error:
            raise item.error
        return item.result

    def checkout(self, timeout=30):
        """Get an available page. Must be called from pool thread."""
        try:
            return self._page_pool.get(timeout=timeout)
        except queue.Empty:
            return None

    def checkin(self, page):
        """Return a page to the pool. Must be called from pool thread."""
        self._page_pool.put(page)

    def reset_page(self, page):
        """Reload the app on a page. Must be called from pool thread."""
        page.goto(self._app_url, wait_until="networkidle")
        page.wait_for_timeout(500)

    def stop(self):
        """Shut down the pool thread and all browsers."""
        if not self._started:
            return
        self._stop_event.set()
        self._work_queue.put(None)  # poison pill
        if self._thread:
            self._thread.join(timeout=30)
        self._started = False

    @property
    def available(self):
        return self._page_pool.qsize()

    @property
    def total(self):
        return self._size
