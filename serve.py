"""Local HTTP server for the asset editor app.

Run:  python serve.py
Then open:  http://localhost:8080

Serves app files and proxies /comfyui/* requests to ComfyUI
so the browser doesn't hit CORS issues.
Auto-launches ComfyUI desktop app if not already running.
"""

import http.server
import os
import subprocess
import time
import urllib.request
import urllib.error
import json as _json
import threading

PORT = 8080
COMFYUI_PORT = 8000
COMFYUI_BASE = f"http://127.0.0.1:{COMFYUI_PORT}"
COMFYUI_EXE = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\ComfyUI\ComfyUI.exe"
)
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# API layer (initialized in __main__)
api_router = None
api_pool = None

def find_comfyui_port():
    """Scan common ports to find a running ComfyUI instance."""
    for port in [COMFYUI_PORT, 8188, 8189, 8000, 8001]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/system_stats")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return port
        except Exception:
            pass
    return None

def ensure_comfyui_running():
    """Launch ComfyUI desktop app if not already running."""
    global COMFYUI_BASE

    found = find_comfyui_port()
    if found:
        COMFYUI_BASE = f"http://127.0.0.1:{found}"
        print(f"ComfyUI already running at {COMFYUI_BASE}")
        return True

    if not os.path.exists(COMFYUI_EXE):
        print(f"ComfyUI not found at {COMFYUI_EXE} — skipping auto-launch.")
        return False

    print(f"Starting ComfyUI from {COMFYUI_EXE}...")
    subprocess.Popen(
        [COMFYUI_EXE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS
    )

    # Wait up to 90 seconds, scanning multiple ports
    for i in range(90):
        time.sleep(1)
        found = find_comfyui_port()
        if found:
            COMFYUI_BASE = f"http://127.0.0.1:{found}"
            print(f"ComfyUI ready at {COMFYUI_BASE} (took {i+1}s)")
            return True
        if i % 10 == 9:
            print(f"  Still waiting for ComfyUI... ({i+1}s)")

    print("ComfyUI did not become reachable within 90s. Continuing without it.")
    return False

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
        elif self.path.startswith("/comfyui/"):
            self._proxy("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._handle_api("POST")
        elif self.path == "/save-mask":
            self._save_mask()
        elif self.path.startswith("/comfyui/"):
            self._proxy("POST")
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

    def _save_mask(self):
        """Download mask from ComfyUI and save as local static file."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            import json as _json
            params = _json.loads(body) if body else {}
            filename = params.get("filename", "")
            subfolder = params.get("subfolder", "")
            img_type = params.get("type", "output")
            if '..' in filename or '..' in subfolder or '/' in filename or '\\' in filename:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Invalid filename")
                return
            # Download directly from ComfyUI server-side (no CORS issues)
            url = f"{COMFYUI_BASE}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            mask_path = os.path.join(DIRECTORY, "_temp_mask.png")
            with open(mask_path, "wb") as f:
                f.write(data)
            # Fix premultiplied-alpha issue: ComfyUI may output RGBA PNGs
            # with alpha=0 but mask data in RGB. Browsers destroy RGB when
            # alpha=0 due to premultiplied-alpha compositing in Canvas.
            # Set alpha to 255 so the browser can read the RGB mask data.
            try:
                from PIL import Image
                img = Image.open(mask_path)
                if img.mode == "RGBA":
                    import numpy as np
                    arr = np.array(img)
                    if arr[:, :, 3].max() == 0 and arr[:, :, :3].max() > 0:
                        arr[:, :, 3] = 255
                        Image.fromarray(arr).save(mask_path)
            except Exception:
                pass  # Non-critical: if PIL isn't available, skip the fix
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"ok":true,"size":{len(data)}}}'.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Save mask error: {e}".encode())

    def _proxy(self, method):
        target_path = self.path[len("/comfyui"):]  # strip /comfyui prefix
        if '..' in target_path:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid proxy path")
            return
        url = COMFYUI_BASE + target_path
        try:
            body = None
            headers = {}
            if method == "POST":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length > 0 else None
                ct = self.headers.get("Content-Type")
                if ct:
                    headers["Content-Type"] = ct

            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for key in ("Content-Type", "Content-Length"):
                    val = resp.headers.get(key)
                    if val:
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Proxy error: {e}".encode())

    def log_message(self, format, *args):
        # Quieter logging - only show errors and proxy requests
        msg = format % args
        if "/api/" in msg or "/comfyui/" in msg or "error" in msg.lower() or "40" in msg or "50" in msg:
            super().log_message(format, *args)

if __name__ == "__main__":
    ensure_comfyui_running()

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
    from api.endpoints import workflow as ep_workflow
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
    ep_workflow.register(api_router)
    ep_border_detect.register(api_router)

    # ThreadingHTTPServer handles each request in its own thread.
    # The Playwright pool runs its own dedicated thread internally —
    # all page operations are dispatched to it via run_on_page().
    class ThreadingServer(http.server.ThreadingHTTPServer):
        daemon_threads = True

    with ThreadingServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        print(f"API at http://127.0.0.1:{PORT}/api/*")
        print(f"ComfyUI proxy at http://127.0.0.1:{PORT}/comfyui/*")
        print(f"ComfyUI backend: {COMFYUI_BASE}")
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
