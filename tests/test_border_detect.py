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


def test_api_endpoint_handler():
    """The border_detect endpoint handler should accept params and return border_map."""
    from api.endpoints.border_detect import _handle_border_detect
    import base64
    from PIL import Image
    import io

    img = Image.new("RGB", (20, 20), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    handler = _handle_border_detect()
    status, response = handler({"image": img_b64, "width": 20, "height": 20, "mode": "general"})
    assert status == 200
    assert "border_map" in response
    assert "techniques_run" in response
    assert response["techniques_run"] >= 40


def test_edge_techniques_produce_output():
    """Each edge technique should return a (H, W) float32 array with some non-zero values."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.edge import TECHNIQUES
    import cv2

    img = np.zeros((50, 50, 3), dtype=np.uint8)
    img[:, 25:, :] = 255
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (50, 50), f"{tid} wrong shape: {result.shape}"
        assert result.dtype == np.float32, f"{tid} wrong dtype: {result.dtype}"
        assert result.max() > 0, f"{tid} returned all zeros on image with clear edge"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_color_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.color import TECHNIQUES
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    img[:, :25, :] = [40, 30, 25]
    img[:, 25:, :] = [200, 180, 160]
    # Add achromatic dark border so dark/achromatic detectors fire
    img[0:4, :, :] = [15, 15, 15]
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (50, 50), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_morphological_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.morphological import TECHNIQUES
    img = np.full((80, 80, 3), 200, dtype=np.uint8)
    img[10:70, 10:70, :] = 100
    img[8:12, 8:72, :] = 30; img[68:72, 8:72, :] = 30
    img[8:72, 8:12, :] = 30; img[8:72, 68:72, :] = 30
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (80, 80), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_texture_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.texture import TECHNIQUES
    img = np.random.randint(50, 200, (60, 60, 3), dtype=np.uint8)
    img[:, 30:, :] = 128
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_statistical_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.statistical import TECHNIQUES
    img = np.random.randint(50, 200, (60, 60, 3), dtype=np.uint8)
    img[:, 30:, :] = 128
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_gradient_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.gradient import TECHNIQUES
    img = np.full((60, 60, 3), 50, dtype=np.uint8)
    img[15:45, 15:45, :] = 200
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_structural_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.structural import TECHNIQUES
    import cv2 as cv2_test
    img = np.full((80, 80, 3), 220, dtype=np.uint8)
    cv2_test.rectangle(img, (10, 10), (70, 70), (30, 30, 30), 3)
    cv2_test.rectangle(img, (20, 20), (60, 60), (30, 30, 30), 3)
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (80, 80), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_adaptive_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.adaptive import TECHNIQUES
    import cv2 as cv2_test
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:, 32:, :] = 255
    noise = np.random.randint(0, 30, img.shape, dtype=np.uint8)
    img = cv2_test.add(img, noise)
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (64, 64), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"


def test_quantization_techniques_produce_output():
    from border_detect.preprocess import preprocess
    from border_detect.techniques.quantization import TECHNIQUES
    img = np.full((60, 60, 3), 200, dtype=np.uint8)
    img[10:50, 10:50, :] = 100
    img[8:12, 8:52, :] = 30; img[48:52, 8:52, :] = 30
    img[8:52, 8:12, :] = 30; img[8:52, 48:52, :] = 30
    preprocessed = preprocess(img)
    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
