"""Unit tests for quality metric helper functions.

Run: .venv/Scripts/python.exe -m pytest tests/test_unit_metrics.py -v
"""
import numpy as np
import pytest
from PIL import Image

from helpers.quality_metrics import (
    alpha_stats,
    alpha_iou,
    alpha_mae,
    region_opaque_pct,
    pixel_diff_count,
    compute_ssim,
    compute_psnr,
    compute_phash_distance,
    run_quality_gates,
)


@pytest.mark.unit
class TestAlphaStats:
    def test_fully_transparent(self):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        stats = alpha_stats(img)
        assert stats["transparent"] == 100.0
        assert stats["semi"] == 0.0
        assert stats["opaque"] == 0.0

    def test_fully_opaque(self):
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        stats = alpha_stats(img)
        assert stats["transparent"] == 0.0
        assert stats["semi"] == 0.0
        assert stats["opaque"] == 100.0

    def test_half_and_half(self):
        arr = np.zeros((10, 10, 4), dtype=np.uint8)
        arr[5:, :, :] = 255
        img = Image.fromarray(arr, "RGBA")
        stats = alpha_stats(img)
        assert stats["transparent"] == 50.0
        assert stats["opaque"] == 50.0
        assert stats["semi"] == 0.0

    def test_semi_transparent(self):
        img = Image.new("RGBA", (10, 10), (100, 100, 100, 128))
        stats = alpha_stats(img)
        assert stats["transparent"] == 0.0
        assert stats["opaque"] == 0.0
        assert stats["semi"] == 100.0


@pytest.mark.unit
class TestAlphaIoU:
    def test_identical_images(self):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        arr = np.array(img)
        arr[3:7, 3:7, 3] = 255
        img = Image.fromarray(arr, "RGBA")
        assert alpha_iou(img, img) == pytest.approx(1.0, abs=0.001)

    def test_no_overlap(self):
        arr_a = np.full((10, 10, 4), 255, dtype=np.uint8)
        arr_a[:5, :, 3] = 0
        img_a = Image.fromarray(arr_a, "RGBA")
        arr_b = np.full((10, 10, 4), 255, dtype=np.uint8)
        arr_b[5:, :, 3] = 0
        img_b = Image.fromarray(arr_b, "RGBA")
        iou = alpha_iou(img_a, img_b)
        assert iou == pytest.approx(0.0, abs=0.001)


@pytest.mark.unit
class TestAlphaMAE:
    def test_identical(self):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 128))
        assert alpha_mae(img, img) == pytest.approx(0.0, abs=0.01)

    def test_max_difference(self):
        img_a = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img_b = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
        assert alpha_mae(img_a, img_b) == pytest.approx(255.0, abs=0.01)


@pytest.mark.unit
class TestRegionOpaque:
    def test_full_region(self):
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        pct = region_opaque_pct(img, 0.0, 1.0, 0.0, 1.0)
        assert pct == pytest.approx(100.0, abs=0.1)

    def test_empty_region(self):
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        pct = region_opaque_pct(img, 0.0, 1.0, 0.0, 1.0)
        assert pct == pytest.approx(0.0, abs=0.1)


@pytest.mark.unit
class TestPixelDiff:
    def test_identical(self):
        img = Image.new("RGBA", (10, 10), (100, 100, 100, 255))
        assert pixel_diff_count(img, img) == 0

    def test_all_different(self):
        img_a = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img_b = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        assert pixel_diff_count(img_a, img_b) == 100


@pytest.mark.unit
class TestSSIM:
    def test_identical(self):
        img = Image.new("RGBA", (32, 32), (128, 128, 128, 255))
        val = compute_ssim(img, img)
        assert val == pytest.approx(1.0, abs=0.01)


@pytest.mark.unit
class TestPSNR:
    def test_identical(self):
        img = Image.new("RGBA", (32, 32), (128, 128, 128, 255))
        val = compute_psnr(img, img)
        assert val == float("inf")


@pytest.mark.unit
class TestPHash:
    def test_identical(self):
        img = Image.new("RGBA", (64, 64), (128, 128, 128, 255))
        assert compute_phash_distance(img, img) == 0

    def test_very_different(self):
        img_a = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
        img_b = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
        dist = compute_phash_distance(img_a, img_b)
        assert dist > 0


@pytest.mark.unit
class TestQualityGates:
    def test_identical_passes_all(self):
        arr = np.random.randint(0, 255, (64, 64, 4), dtype=np.uint8)
        img = Image.fromarray(arr, "RGBA")
        result = run_quality_gates(img, img)
        assert result["passed"] is True
        assert len(result["failures"]) == 0

    def test_totally_different_fails(self):
        img_a = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        img_b = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
        result = run_quality_gates(img_a, img_b)
        assert result["passed"] is False
        assert len(result["failures"]) > 0
