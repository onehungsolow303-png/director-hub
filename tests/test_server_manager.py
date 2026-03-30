"""Tests for server_manager helper — detection and staleness logic."""

import time
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from helpers.server_manager import (
    is_comfyui_running,
    is_serve_running,
    is_serve_stale,
    SOURCE_FILES,
)


def test_comfyui_not_running():
    """When no ComfyUI is listening, is_comfyui_running returns None."""
    with patch("helpers.server_manager.urllib.request.urlopen", side_effect=Exception("refused")):
        assert is_comfyui_running() is None


def test_comfyui_running():
    """When ComfyUI responds on a port, return that port."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("helpers.server_manager.urllib.request.urlopen", return_value=mock_resp):
        result = is_comfyui_running()
        assert result is not None


def test_serve_not_running():
    """When serve.py is not listening, is_serve_running returns False."""
    with patch("helpers.server_manager.urllib.request.urlopen", side_effect=Exception("refused")):
        assert is_serve_running() is False


def test_serve_running():
    """When serve.py responds on 8080, is_serve_running returns True."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("helpers.server_manager.urllib.request.urlopen", return_value=mock_resp):
        assert is_serve_running() is True


def test_stale_when_source_newer(tmp_path):
    """Server is stale if any source file was modified after server start."""
    fake_file = tmp_path / "app.js"
    fake_file.write_text("x")
    # server started 10 seconds ago, file modified now
    server_start = time.time() - 10
    assert is_serve_stale(server_start, source_files=[str(fake_file)]) is True


def test_not_stale_when_source_older(tmp_path):
    """Server is NOT stale if all source files are older than server start."""
    fake_file = tmp_path / "app.js"
    fake_file.write_text("x")
    import os
    os.utime(str(fake_file), (time.time() - 100, time.time() - 100))
    server_start = time.time() - 5
    assert is_serve_stale(server_start, source_files=[str(fake_file)]) is False
