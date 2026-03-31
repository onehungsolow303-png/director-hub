"""Tests for the multi-spectrum border detection package."""

import numpy as np
import pytest


def test_preprocess_creates_all_colorspaces():
    """preprocess() should return grayscale, HSV, LAB, YCbCr, and integral images."""
    from border_detect.preprocess import preprocess
    img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
    result = preprocess(img)
    assert "gray" in result
    assert "hsv" in result
    assert "lab" in result
    assert "ycbcr" in result
    assert "integral" in result
    assert "integral_sq" in result
    assert result["gray"].shape == (10, 10)
    assert result["hsv"].shape == (10, 10, 3)


def test_technique_registry_discovers_all():
    """The technique registry should find all 40 techniques."""
    from border_detect.techniques import get_all_techniques
    techniques = get_all_techniques()
    assert len(techniques) >= 40
    for tid, fn in techniques:
        assert isinstance(tid, str)
        assert callable(fn)


def test_detect_borders_returns_confidence_map():
    """detect_borders() should return a dict with border_map array."""
    from border_detect import detect_borders
    img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
    result = detect_borders(img)
    assert "border_map" in result
    assert result["border_map"].shape == (50, 50)
    assert result["border_map"].dtype == np.uint8
    assert "techniques_run" in result
    assert result["techniques_run"] >= 40
