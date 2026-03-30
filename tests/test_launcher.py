"""Tests for launcher.py — verify it parses args and calls server_manager."""

from unittest.mock import patch, MagicMock

import pytest


def test_launcher_imports():
    """launcher.py should be importable."""
    import importlib
    mod = importlib.import_module("launcher")
    assert hasattr(mod, "main")


def test_launcher_calls_ensure_services():
    """main() should call ensure_services before running pytest."""
    with patch("launcher.server_manager") as mock_sm:
        mock_sm.ensure_services.return_value = (8000, True)
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            from launcher import main
            result = main(["--co"])  # --co is pytest dry-run
            mock_sm.ensure_services.assert_called_once()
