"""Test launcher — boots ComfyUI + serve.py, then runs pytest.

Usage:
    .venv/Scripts/python.exe tests/launcher.py [pytest args...]

Examples:
    .venv/Scripts/python.exe tests/launcher.py -v
    .venv/Scripts/python.exe tests/launcher.py tests/test_production.py -v
    .venv/Scripts/python.exe tests/launcher.py -m smoke -v
    .venv/Scripts/python.exe tests/launcher.py --production-loop

The launcher:
1. Detects if ComfyUI is running — launches it if not
2. Detects if serve.py is running — launches it if not
3. Checks if serve.py is stale (source files changed) — restarts if so
4. Runs pytest with all forwarded arguments
5. Cleans up serve.py on exit (ComfyUI stays running)
"""

import atexit
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Dev\Image generator")
VENV_PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")

# Add tests/ to path so helpers are importable
sys.path.insert(0, str(ROOT / "tests"))

from helpers import server_manager


def main(args=None):
    """Boot services and run pytest with given args."""
    if args is None:
        args = sys.argv[1:]

    # Check for --production-loop flag
    production_loop = "--production-loop" in args
    if production_loop:
        args = [a for a in args if a != "--production-loop"]

    # Boot services
    comfyui_port, serve_ok = server_manager.ensure_services()

    if not serve_ok:
        print("FATAL: serve.py failed to start. Cannot run tests.")
        return 1

    # Register cleanup
    atexit.register(server_manager.shutdown)

    if production_loop:
        # Run the production loop script directly
        result = subprocess.run(
            [VENV_PYTHON, str(ROOT / "tests" / "production_loop.py")] + args,
            cwd=str(ROOT),
        )
        return result.returncode

    # Run pytest with forwarded args
    pytest_args = [VENV_PYTHON, "-m", "pytest"] + args
    result = subprocess.run(pytest_args, cwd=str(ROOT))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
