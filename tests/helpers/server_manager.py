"""Server manager — detect, launch, and manage ComfyUI + serve.py for tests.

Handles:
- ComfyUI: detect on ports 8000/8188/8189, launch Electron app if missing
- serve.py: detect on port 8080, launch as subprocess, staleness restart
- Health checks: wait for both services to respond before returning
"""

import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Dev\Image generator")
SERVE_PY = ROOT / "serve.py"
VENV_PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")
COMFYUI_EXE = os.path.expandvars(r"%LOCALAPPDATA%\Programs\ComfyUI\ComfyUI.exe")

COMFYUI_PORTS = [8000, 8188, 8189, 8001]
SERVE_PORT = 8080
SERVE_URL = f"http://127.0.0.1:{SERVE_PORT}"

# Files whose modification time determines staleness
SOURCE_FILES = [
    str(ROOT / "serve.py"),
    str(ROOT / "app.js"),
    str(ROOT / "index.html"),
    str(ROOT / "styles.css"),
]

# Module-level state for the serve.py subprocess we launched
_serve_process = None


def is_comfyui_running():
    """Check if ComfyUI is responding on any known port.

    Returns the port number if found, None otherwise.
    """
    for port in COMFYUI_PORTS:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/system_stats")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return port
        except Exception:
            pass
    return None


def is_serve_running():
    """Check if serve.py is responding on port 8080.

    Returns True if reachable, False otherwise.
    """
    try:
        req = urllib.request.Request(SERVE_URL)
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_serve_stale(server_start_time, source_files=None):
    """Check if any source file was modified after the server started.

    Args:
        server_start_time: epoch timestamp when the server process started.
        source_files: list of file paths to check. Defaults to SOURCE_FILES.

    Returns True if any source file is newer than server_start_time.
    """
    files = source_files if source_files is not None else SOURCE_FILES
    for fpath in files:
        try:
            mtime = os.path.getmtime(fpath)
            if mtime > server_start_time:
                return True
        except OSError:
            pass
    return False


def _find_serve_process():
    """Find a running serve.py process and return (pid, create_time) or None."""
    try:
        import psutil
    except ImportError:
        return None
    for proc in psutil.process_iter(["pid", "cmdline", "create_time"]):
        try:
            cmdline = proc.info["cmdline"] or []
            if any("serve.py" in arg for arg in cmdline):
                return proc.info["pid"], proc.info["create_time"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None


def _kill_serve_process():
    """Kill any running serve.py process."""
    try:
        import psutil
    except ImportError:
        return
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"] or []
            if any("serve.py" in arg for arg in cmdline):
                proc.terminate()
                proc.wait(timeout=5)
                print(f"  Terminated stale serve.py (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass


def _wait_for_url(url, timeout=30, label="service"):
    """Poll a URL until it responds 200 or timeout."""
    for i in range(timeout):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        if i % 10 == 9:
            print(f"  Still waiting for {label}... ({i+1}s)")
        time.sleep(1)
    return False


def start_comfyui():
    """Launch ComfyUI Electron app if not already running.

    Returns the port ComfyUI is running on, or None if it failed.
    """
    port = is_comfyui_running()
    if port:
        print(f"  ComfyUI already running on port {port}")
        return port

    if not os.path.exists(COMFYUI_EXE):
        print(f"  ComfyUI not found at {COMFYUI_EXE} — cannot auto-launch")
        return None

    print(f"  Launching ComfyUI from {COMFYUI_EXE}...")
    subprocess.Popen(
        [COMFYUI_EXE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
    )

    # Wait up to 90s, scanning all known ports
    for i in range(90):
        time.sleep(1)
        port = is_comfyui_running()
        if port:
            print(f"  ComfyUI ready on port {port} (took {i+1}s)")
            return port
        if i % 10 == 9:
            print(f"  Still waiting for ComfyUI... ({i+1}s)")

    print("  ComfyUI did not start within 90s")
    return None


def start_serve(comfyui_port=None):
    """Launch serve.py if not running, or restart if stale.

    Returns True if serve.py is running and up-to-date after this call.
    """
    global _serve_process

    # Check if already running
    if is_serve_running():
        # Check staleness
        proc_info = _find_serve_process()
        if proc_info:
            pid, create_time = proc_info
            if is_serve_stale(create_time):
                print(f"  serve.py (PID {pid}) is stale — source files changed since startup")
                _kill_serve_process()
                time.sleep(1)
            else:
                print(f"  serve.py already running (PID {pid}), up to date")
                return True

    # Launch serve.py
    print(f"  Starting serve.py...")
    env = os.environ.copy()
    if comfyui_port:
        env["COMFYUI_PORT"] = str(comfyui_port)

    _serve_process = subprocess.Popen(
        [VENV_PYTHON, str(SERVE_PY)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    if not _wait_for_url(SERVE_URL, timeout=30, label="serve.py"):
        print("  serve.py did not become reachable within 30s")
        return False

    print(f"  serve.py ready at {SERVE_URL} (PID {_serve_process.pid})")
    return True


def ensure_services():
    """Boot ComfyUI + serve.py if needed. Restart serve.py if stale.

    This is the main entry point. Call it before running any tests.
    Returns (comfyui_port, serve_ok) tuple.
    """
    print("\n== Service Manager ==")

    comfyui_port = start_comfyui()
    if comfyui_port is None:
        print("  WARNING: ComfyUI not available — AI tests will fail")

    serve_ok = start_serve(comfyui_port)
    if not serve_ok:
        print("  WARNING: serve.py not available — all browser tests will fail")

    print(f"  Services: ComfyUI={'port ' + str(comfyui_port) if comfyui_port else 'DOWN'}"
          f" | serve.py={'UP' if serve_ok else 'DOWN'}")
    print()
    return comfyui_port, serve_ok


def shutdown():
    """Stop serve.py if we launched it. ComfyUI is left running (Electron app)."""
    global _serve_process
    if _serve_process and _serve_process.poll() is None:
        print("\n  Stopping serve.py...")
        _serve_process.terminate()
        try:
            _serve_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _serve_process.kill()
        _serve_process = None
