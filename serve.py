"""Local HTTP server for the Gut It Out asset editor app.

Run:  python serve.py
Then open:  http://localhost:8080

Serves app files and Python API endpoints for extraction,
border detection, mask operations, and image enhancement.
"""

import http.server
import os
import time
import json as _json
import threading

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# API layer (initialized in __main__)
api_router = None
api_pool = None

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        origin = self.headers.get("Origin", "")
        allowed_origins = {"http://127.0.0.1:8080", "http://localhost:8080"}
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8080")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._handle_api("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._handle_api("POST")
        else:
            self.send_response(405)
            self.end_headers()

    def _handle_api(self, method):
        body = None
        if method == "POST":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode() if content_length > 0 else ""
        status, response = api_router.handle_request(self, method, self.path, body)
        api_router.send_json(self, status, response)

    def log_message(self, format, *args):
        # Quieter logging - only show API requests and errors
        msg = format % args
        if "/api/" in msg or "error" in msg.lower() or "40" in msg or "50" in msg:
            super().log_message(format, *args)

if __name__ == "__main__":
    # Initialize API layer
    from api.jobs import JobManager
    from api.pool import PlaywrightPool
    from api.bridge import AppBridge
    from api.router import APIRouter
    from api.endpoints import extract as ep_extract
    from api.endpoints import config as ep_config
    from api.endpoints import mask as ep_mask
    from api.endpoints import enhance as ep_enhance
    from api.endpoints import split as ep_split
    from api.endpoints import border_detect as ep_border_detect

    job_manager = JobManager()
    api_pool = PlaywrightPool(f"http://127.0.0.1:{PORT}", size=2)
    bridge = AppBridge()
    api_router = APIRouter(job_manager, api_pool, bridge)

    # Register all endpoints
    ep_extract.register(api_router)
    ep_config.register(api_router)
    ep_mask.register(api_router)
    ep_enhance.register(api_router)
    ep_split.register(api_router)
    ep_border_detect.register(api_router)

    # ThreadingHTTPServer handles each request in its own thread.
    # The Playwright pool runs its own dedicated thread internally —
    # all page operations are dispatched to it via run_on_page().
    class ThreadingServer(http.server.ThreadingHTTPServer):
        daemon_threads = True

    with ThreadingServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        print(f"API at http://127.0.0.1:{PORT}/api/*")
        print(f"Directory: {DIRECTORY}")

        # Start Playwright pool (runs its own thread, blocks until ready)
        def _start_pool():
            time.sleep(2)
            print("Starting Playwright pool (2 workers)...")
            api_pool.start()
            print("Playwright pool ready.")
        pool_thread = threading.Thread(target=_start_pool, daemon=True)
        pool_thread.start()

        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            if api_pool:
                api_pool.stop()
