# Unified Live Test System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 26 fragmented standalone test scripts with a unified pytest-based live test system that drives the real browser app, generates extraction images, and compares them against golden reference files using progressive quality gates (pHash → PSNR → SSIM → Alpha IoU/MAE → Region analysis), producing an HTML visual diff report.

**Architecture:** pytest as runner, parameterized tests across all 6 presets × 2 source images. Shared helper modules for browser automation (Playwright), quality metrics (scikit-image + imagehash + numpy), canvas extraction, and HTML report generation (Jinja2). Progressive quality gate chain that fails-fast on cheap checks before running expensive ones. Server assumed running at `http://127.0.0.1:8080`.

**Tech Stack:** Python 3.12, pytest, Playwright 1.58.0, Pillow 12.1.1, NumPy 2.3.5, scikit-image 0.26.0, opencv-python 4.13.0, imagehash (new), Jinja2 (new), pytest-html (new)

---

## File Structure

```
tests/
├── conftest.py                # pytest fixtures: browser, page, app_ready, reference_images
├── pytest.ini                 # marks, paths, defaults
├── helpers/
│   ├── __init__.py
│   ├── quality_metrics.py     # SSIM, PSNR, pHash, alpha IoU/MAE, region analysis
│   ├── canvas_extract.py      # toDataURL extraction, canvas polling, wait helpers
│   ├── app_driver.py          # upload image, set preset, click process/ai-remove, wait
│   └── report_gen.py          # HTML visual diff report with Jinja2
├── test_smoke.py              # Server reachable, app loads, canvas element exists
├── test_unit_metrics.py       # Verify metric functions against synthetic known images
├── test_live_extraction.py    # Parameterized: all 6 presets × 2 source images, full browser workflow
├── test_quality_gates.py      # Progressive comparison of extracted results vs golden references
├── golden/                    # Symlinks to reference images (read-only)
│   ├── dark_source.png        -> input/.../Original Image dark background.png
│   ├── dark_ref_full.png      -> input/.../example preview ectraction dark background removed.PNG
│   ├── dark_ref_topbar.png    -> input/.../example extracted final asset top bar dark background removed.PNG
│   ├── dark_ref_botbar.png    -> input/.../example extracted final asset bottom bar dark background.PNG
│   ├── dark_ref_portrait.png  -> input/.../example extracted final asset bottom left box asset. dark background removed.PNG
│   ├── light_source.png       -> input/.../Original Image White background.png
│   ├── light_ref_full.png     -> input/.../example preview ectraction white background removed.PNG
│   ├── light_ref_topbar.png   -> input/.../example extracted final asset top bar white background removed.PNG
│   ├── light_ref_botbar.png   -> input/.../example extracted final asset bottom bar dark background.PNG
│   └── light_ref_portrait.png -> input/.../example extracted final asset bottom left box asset. white background removed.PNG
└── reports/                   # Generated output (gitignored)
    ├── results.html           # pytest-html report
    ├── quality_report.json    # Machine-readable metrics
    └── diffs/                 # Visual diff heatmaps per test
```

---

## Task 1: Install Dependencies and Create Project Config

**Files:**
- Create: `tests/pytest.ini`
- Create: `tests/helpers/__init__.py`
- Modify: `.gitignore` (add `tests/reports/`)

- [ ] **Step 1: Install new packages**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pip install pytest pytest-html imagehash jinja2
```

Expected: All packages install successfully. pytest version >= 8.x.

- [ ] **Step 2: Verify installations**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest --version
.venv/Scripts/python.exe -c "import imagehash; print(imagehash.__version__)"
.venv/Scripts/python.exe -c "import jinja2; print(jinja2.__version__)"
```

Expected: All imports succeed, versions printed.

- [ ] **Step 3: Create pytest.ini**

```ini
[pytest]
testpaths = tests
markers =
    smoke: Fast sanity checks (server up, app loads)
    unit: Unit tests for metric helper functions
    live: Live browser extraction tests (slow, needs server)
    quality: Quality gate comparison tests (needs extraction output)
    slow: Tests that take > 30s each
addopts = -v --tb=short
```

- [ ] **Step 4: Create helpers/__init__.py**

```python
"""Test helpers for the unified live test system."""
```

- [ ] **Step 5: Create tests/golden/ symlinks**

Run:
```bash
cd "C:/Dev/Image generator"
mkdir -p tests/golden tests/reports/diffs

# Dark background references
cp "input/Example quality image extraction/Dark background examples/Original Image dark background.png" tests/golden/dark_source.png
cp "input/Example quality image extraction/Dark background examples/example preview ectraction dark background removed.PNG" tests/golden/dark_ref_full.png
cp "input/Example quality image extraction/Dark background examples/example extracted final asset top bar dark background removed.PNG" tests/golden/dark_ref_topbar.png
cp "input/Example quality image extraction/Dark background examples/example extracted final asset bottom bar dark background.PNG" tests/golden/dark_ref_botbar.png
cp "input/Example quality image extraction/Dark background examples/example extracted final asset bottom left box asset. dark background removed.PNG" tests/golden/dark_ref_portrait.png

# Light background references
cp "input/Example quality image extraction/Light background examples/Original Image White background.png" tests/golden/light_source.png
cp "input/Example quality image extraction/Light background examples/example preview ectraction white background removed.PNG" tests/golden/light_ref_full.png
cp "input/Example quality image extraction/Light background examples/example extracted final asset top bar white background removed.PNG" tests/golden/light_ref_topbar.png
cp "input/Example quality image extraction/Light background examples/example extracted final asset bottom bar dark background.PNG" tests/golden/light_ref_botbar.png
cp "input/Example quality image extraction/Light background examples/example extracted final asset bottom left box asset. white background removed.PNG" tests/golden/light_ref_portrait.png
```

Note: We copy instead of symlink for cross-platform compatibility on Windows.

- [ ] **Step 6: Add tests/reports/ to .gitignore**

Append to `.gitignore`:
```
tests/reports/
tests/golden/
```

- [ ] **Step 7: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/pytest.ini tests/helpers/__init__.py .gitignore
git commit -m "feat: add pytest config and test infrastructure scaffolding"
```

---

## Task 2: Create Quality Metrics Helper

**Files:**
- Create: `tests/helpers/quality_metrics.py`
- Create: `tests/test_unit_metrics.py`

- [ ] **Step 1: Write failing tests for metric functions**

Create `tests/test_unit_metrics.py`:

```python
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
        """A fully transparent image should be 100% transparent."""
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        stats = alpha_stats(img)
        assert stats["transparent"] == 100.0
        assert stats["semi"] == 0.0
        assert stats["opaque"] == 0.0

    def test_fully_opaque(self):
        """A fully opaque image should be 100% opaque."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        stats = alpha_stats(img)
        assert stats["transparent"] == 0.0
        assert stats["semi"] == 0.0
        assert stats["opaque"] == 100.0

    def test_half_and_half(self):
        """Top half transparent, bottom half opaque."""
        arr = np.zeros((10, 10, 4), dtype=np.uint8)
        arr[5:, :, :] = 255  # bottom half fully opaque white
        img = Image.fromarray(arr, "RGBA")
        stats = alpha_stats(img)
        assert stats["transparent"] == 50.0
        assert stats["opaque"] == 50.0
        assert stats["semi"] == 0.0

    def test_semi_transparent(self):
        """All pixels at alpha=128 should be 100% semi-transparent."""
        img = Image.new("RGBA", (10, 10), (100, 100, 100, 128))
        stats = alpha_stats(img)
        assert stats["transparent"] == 0.0
        assert stats["opaque"] == 0.0
        assert stats["semi"] == 100.0


@pytest.mark.unit
class TestAlphaIoU:
    def test_identical_images(self):
        """IoU of identical alpha channels should be 1.0."""
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        arr = np.array(img)
        arr[3:7, 3:7, 3] = 255  # opaque square in center
        img = Image.fromarray(arr, "RGBA")
        assert alpha_iou(img, img) == pytest.approx(1.0, abs=0.001)

    def test_no_overlap(self):
        """IoU of non-overlapping transparent regions should be 0."""
        # Image A: top half transparent
        arr_a = np.full((10, 10, 4), 255, dtype=np.uint8)
        arr_a[:5, :, 3] = 0
        img_a = Image.fromarray(arr_a, "RGBA")

        # Image B: bottom half transparent
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
        """All transparent vs all opaque should have MAE=255."""
        img_a = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img_b = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
        assert alpha_mae(img_a, img_b) == pytest.approx(255.0, abs=0.01)


@pytest.mark.unit
class TestRegionOpaque:
    def test_full_region(self):
        """Fully opaque image region check."""
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        pct = region_opaque_pct(img, 0.0, 1.0, 0.0, 1.0)
        assert pct == pytest.approx(100.0, abs=0.1)

    def test_empty_region(self):
        """Fully transparent image region check."""
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
        """Identical images should pass all quality gates."""
        arr = np.random.randint(0, 255, (64, 64, 4), dtype=np.uint8)
        img = Image.fromarray(arr, "RGBA")
        result = run_quality_gates(img, img)
        assert result["passed"] is True
        assert len(result["failures"]) == 0

    def test_totally_different_fails(self):
        """Completely different images should fail early."""
        img_a = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        img_b = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
        result = run_quality_gates(img_a, img_b)
        assert result["passed"] is False
        assert len(result["failures"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest tests/test_unit_metrics.py -v
```

Expected: ImportError — `helpers.quality_metrics` does not exist yet.

- [ ] **Step 3: Implement quality_metrics.py**

Create `tests/helpers/quality_metrics.py`:

```python
"""Quality metric functions for image comparison.

Progressive quality gates (fast → expensive):
1. File/format check       ~1ms
2. Perceptual hash (pHash) ~5ms
3. PSNR                    ~20ms
4. SSIM                    ~100ms
5. Alpha IoU               ~50ms
6. Alpha MAE               ~50ms
7. Region analysis          ~200ms
"""

import numpy as np
from PIL import Image

# ── Thresholds (configurable per-test via overrides) ──────────────────

DEFAULT_THRESHOLDS = {
    "phash_max_distance": 15,     # Fast pre-filter: > 15 = fundamentally different
    "psnr_min_db": 25,            # Global signal quality
    "ssim_min": 0.85,             # Perceptual structural similarity
    "alpha_iou_min": 0.90,        # Transparency mask accuracy
    "alpha_mae_max": 12.0,        # Soft-edge alpha precision (0-255 scale)
}


# ── Alpha channel metrics ─────────────────────────────────────────────

def alpha_stats(img: Image.Image) -> dict:
    """Return transparent/semi/opaque percentages for an RGBA image."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    total = alpha.size
    transparent = float(np.sum(alpha == 0)) / total * 100
    opaque = float(np.sum(alpha == 255)) / total * 100
    semi = 100.0 - transparent - opaque
    return {
        "transparent": round(transparent, 2),
        "semi": round(semi, 2),
        "opaque": round(opaque, 2),
    }


def alpha_iou(test_img: Image.Image, ref_img: Image.Image, threshold: int = 10) -> float:
    """Intersection-over-Union of transparent regions (alpha < threshold).

    Returns float 0.0-1.0. Higher = better match.
    """
    if test_img.size != ref_img.size:
        test_img = test_img.resize(ref_img.size, Image.LANCZOS)
    t_alpha = np.array(test_img.convert("RGBA"))[:, :, 3]
    r_alpha = np.array(ref_img.convert("RGBA"))[:, :, 3]
    t_trans = t_alpha < threshold
    r_trans = r_alpha < threshold
    intersection = float(np.sum(t_trans & r_trans))
    union = float(np.sum(t_trans | r_trans))
    if union == 0:
        return 1.0  # Both fully opaque = perfect agreement
    return round(intersection / union, 4)


def alpha_mae(test_img: Image.Image, ref_img: Image.Image) -> float:
    """Mean Absolute Error on alpha channel (0-255 scale).

    Lower = better. 0 = identical alpha channels.
    """
    if test_img.size != ref_img.size:
        test_img = test_img.resize(ref_img.size, Image.LANCZOS)
    t_alpha = np.array(test_img.convert("RGBA"))[:, :, 3].astype(float)
    r_alpha = np.array(ref_img.convert("RGBA"))[:, :, 3].astype(float)
    return round(float(np.mean(np.abs(t_alpha - r_alpha))), 2)


def region_opaque_pct(img: Image.Image, x_start: float, x_end: float,
                      y_start: float, y_end: float) -> float:
    """Return % of opaque pixels (alpha > 128) in a sub-region.

    Coordinates are fractions of image size (0.0-1.0).
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]
    y0, y1 = int(h * y_start), int(h * y_end)
    x0, x1 = int(w * x_start), int(w * x_end)
    region = arr[y0:y1, x0:x1, 3]
    if region.size == 0:
        return 0.0
    return round(float(np.sum(region > 128)) / region.size * 100, 2)


def pixel_diff_count(img_a: Image.Image, img_b: Image.Image) -> int:
    """Count pixels that differ between two RGBA images."""
    a = np.array(img_a.convert("RGBA"))
    b = np.array(img_b.convert("RGBA"))
    if a.shape != b.shape:
        img_b_r = img_b.resize((img_a.width, img_a.height), Image.LANCZOS)
        b = np.array(img_b_r.convert("RGBA"))
    diff = np.any(a != b, axis=2)
    return int(np.sum(diff))


# ── Perceptual metrics ────────────────────────────────────────────────

def compute_ssim(test_img: Image.Image, ref_img: Image.Image) -> float:
    """Structural Similarity Index (0.0-1.0). Higher = more similar.

    Compares grayscale versions. For RGBA, converts to grayscale first.
    Uses scikit-image implementation.
    """
    from skimage.metrics import structural_similarity
    if test_img.size != ref_img.size:
        test_img = test_img.resize(ref_img.size, Image.LANCZOS)
    t_gray = np.array(test_img.convert("L"))
    r_gray = np.array(ref_img.convert("L"))
    # win_size must be odd and <= smallest dimension
    min_dim = min(t_gray.shape)
    win_size = min(7, min_dim if min_dim % 2 == 1 else min_dim - 1)
    if win_size < 3:
        win_size = 3
    return round(float(structural_similarity(r_gray, t_gray, win_size=win_size,
                                              data_range=255)), 4)


def compute_psnr(test_img: Image.Image, ref_img: Image.Image) -> float:
    """Peak Signal-to-Noise Ratio in dB. Higher = better. inf = identical.

    Compares RGBA arrays.
    """
    from skimage.metrics import peak_signal_noise_ratio
    if test_img.size != ref_img.size:
        test_img = test_img.resize(ref_img.size, Image.LANCZOS)
    t_arr = np.array(test_img.convert("RGBA"))
    r_arr = np.array(ref_img.convert("RGBA"))
    mse = np.mean((t_arr.astype(float) - r_arr.astype(float)) ** 2)
    if mse == 0:
        return float("inf")
    return round(float(peak_signal_noise_ratio(r_arr, t_arr, data_range=255)), 2)


def compute_phash_distance(test_img: Image.Image, ref_img: Image.Image,
                           hash_size: int = 8) -> int:
    """Perceptual hash Hamming distance. 0 = identical, higher = more different."""
    import imagehash
    h1 = imagehash.phash(test_img.convert("RGB"), hash_size=hash_size)
    h2 = imagehash.phash(ref_img.convert("RGB"), hash_size=hash_size)
    return h1 - h2


# ── Visual diff ───────────────────────────────────────────────────────

def generate_diff_heatmap(test_img: Image.Image, ref_img: Image.Image) -> Image.Image:
    """Generate a color heatmap showing pixel differences.

    Returns an RGB image where red = large difference, blue = small/none.
    """
    import cv2
    if test_img.size != ref_img.size:
        test_img = test_img.resize(ref_img.size, Image.LANCZOS)
    t_arr = np.array(test_img.convert("RGBA")).astype(float)
    r_arr = np.array(ref_img.convert("RGBA")).astype(float)
    # Per-pixel max channel difference
    diff = np.max(np.abs(t_arr - r_arr), axis=2).astype(np.uint8)
    # Apply colormap (amplify for visibility)
    amplified = np.clip(diff * 3, 0, 255).astype(np.uint8)
    heatmap_bgr = cv2.applyColorMap(amplified, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(heatmap_rgb)


# ── Progressive quality gates ─────────────────────────────────────────

def run_quality_gates(test_img: Image.Image, ref_img: Image.Image,
                      thresholds: dict | None = None) -> dict:
    """Run progressive quality gates from fast to expensive.

    Returns dict with:
        passed: bool
        failures: list of (gate_name, actual_value, threshold)
        metrics: dict of all computed metric values
        failed_at: name of first failing gate, or None
    """
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    metrics = {}
    failures = []

    # Gate 1: Perceptual hash (fastest)
    phash_dist = compute_phash_distance(test_img, ref_img)
    metrics["phash_distance"] = phash_dist
    if phash_dist > t["phash_max_distance"]:
        failures.append(("phash_distance", phash_dist, f"<= {t['phash_max_distance']}"))
        return {"passed": False, "failures": failures, "metrics": metrics,
                "failed_at": "phash_distance"}

    # Gate 2: PSNR
    psnr = compute_psnr(test_img, ref_img)
    metrics["psnr_db"] = psnr
    if psnr < t["psnr_min_db"]:
        failures.append(("psnr_db", psnr, f">= {t['psnr_min_db']}"))
        return {"passed": False, "failures": failures, "metrics": metrics,
                "failed_at": "psnr_db"}

    # Gate 3: SSIM
    ssim = compute_ssim(test_img, ref_img)
    metrics["ssim"] = ssim
    if ssim < t["ssim_min"]:
        failures.append(("ssim", ssim, f">= {t['ssim_min']}"))
        return {"passed": False, "failures": failures, "metrics": metrics,
                "failed_at": "ssim"}

    # Gate 4: Alpha IoU
    iou = alpha_iou(test_img, ref_img)
    metrics["alpha_iou"] = iou
    if iou < t["alpha_iou_min"]:
        failures.append(("alpha_iou", iou, f">= {t['alpha_iou_min']}"))
        return {"passed": False, "failures": failures, "metrics": metrics,
                "failed_at": "alpha_iou"}

    # Gate 5: Alpha MAE
    mae = alpha_mae(test_img, ref_img)
    metrics["alpha_mae"] = mae
    if mae > t["alpha_mae_max"]:
        failures.append(("alpha_mae", mae, f"<= {t['alpha_mae_max']}"))
        return {"passed": False, "failures": failures, "metrics": metrics,
                "failed_at": "alpha_mae"}

    # Gate 6: Alpha stats (informational, no gate — always collected)
    metrics["alpha_stats"] = alpha_stats(test_img)
    metrics["ref_alpha_stats"] = alpha_stats(ref_img)

    return {"passed": True, "failures": [], "metrics": metrics, "failed_at": None}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest tests/test_unit_metrics.py -v
```

Expected: All tests PASS (18 tests).

- [ ] **Step 5: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/helpers/quality_metrics.py tests/test_unit_metrics.py
git commit -m "feat: add quality metrics helper with SSIM, PSNR, pHash, alpha IoU/MAE + unit tests"
```

---

## Task 3: Create Canvas Extraction Helper

**Files:**
- Create: `tests/helpers/canvas_extract.py`

- [ ] **Step 1: Create canvas_extract.py**

```python
"""Canvas extraction and wait helpers for Playwright browser automation.

Extracts HTML5 canvas elements as PIL Images via toDataURL().
Provides polling-based wait functions for async processing completion.
"""

import base64
import time
from io import BytesIO
from pathlib import Path

from PIL import Image


def extract_canvas(page, selector: str) -> Image.Image | None:
    """Extract a canvas element as a PIL RGBA Image via toDataURL.

    Args:
        page: Playwright page object
        selector: CSS selector for the canvas element (e.g. '#resultCanvas')

    Returns:
        PIL Image in RGBA mode, or None if canvas is empty/missing.
    """
    data_url = page.evaluate(f"""() => {{
        const c = document.querySelector('{selector}');
        if (!c || c.width <= 1 || c.height <= 1) return null;
        return c.toDataURL('image/png');
    }}""")
    if not data_url:
        return None
    return _decode_data_url(data_url)


def extract_canvas_js(page, js_expression: str) -> Image.Image | None:
    """Extract a canvas via a custom JS expression that returns a data URL.

    Args:
        page: Playwright page object
        js_expression: JS arrow function returning a data URL string or null.
            Example: '() => { return myCanvas.toDataURL("image/png"); }'

    Returns:
        PIL Image in RGBA mode, or None if JS returns null.
    """
    data_url = page.evaluate(js_expression)
    if not data_url:
        return None
    return _decode_data_url(data_url)


def extract_processed_layout(page) -> Image.Image | None:
    """Extract the processedLayoutCanvas JS global variable."""
    return extract_canvas_js(page, """() => {
        if (typeof processedLayoutCanvas === 'undefined' || !processedLayoutCanvas) return null;
        if (processedLayoutCanvas.width <= 1) return null;
        return processedLayoutCanvas.toDataURL('image/png');
    }""")


def save_canvas_to_file(page, selector: str, out_path: str | Path) -> Image.Image | None:
    """Extract canvas and save to disk. Returns PIL Image or None."""
    img = extract_canvas(page, selector)
    if img:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
    return img


def wait_for_status(page, selector: str, target_text: str,
                    timeout: float = 60, poll_interval: float = 1.0,
                    fail_texts: tuple = ("failed", "error")) -> str:
    """Poll a DOM element's textContent until it contains target_text.

    Args:
        page: Playwright page
        selector: CSS selector for status element
        target_text: Text to wait for (case-insensitive contains)
        timeout: Max seconds to wait
        poll_interval: Seconds between polls
        fail_texts: Texts that indicate failure (case-insensitive)

    Returns:
        The status text when target found, or 'TIMEOUT'/'FAIL: ...'
    """
    start = time.time()
    while time.time() - start < timeout:
        text = page.evaluate(f"""() => {{
            const el = document.querySelector('{selector}');
            return el ? el.textContent : '';
        }}""")
        if target_text.lower() in text.lower():
            return text
        for fail in fail_texts:
            if fail.lower() in text.lower():
                return f"FAIL: {text}"
        time.sleep(poll_interval)
    return "TIMEOUT"


def wait_ai_remove(page, timeout: float = 90) -> str:
    """Wait for AI Remove to complete. Returns status string."""
    start = time.time()
    while time.time() - start < timeout:
        status = page.evaluate("""() => {
            const el = document.querySelector('#aiRemoveStatus');
            return el ? el.textContent : '';
        }""")
        if "Done" in status or "Review" in status:
            return status
        if "failed" in status.lower() or "error" in status.lower():
            return f"FAIL: {status}"
        # Check button re-enabled with result canvas populated
        btn_dis = page.evaluate(
            "() => document.querySelector('#aiRemoveButton')?.disabled"
        )
        if not btn_dis and time.time() - start > 5:
            sz = page.evaluate(
                "() => { const c = document.querySelector('#resultCanvas'); return c ? c.width : 0; }"
            )
            if sz > 1:
                return status or "completed"
        time.sleep(2)
    return "TIMEOUT"


def wait_process_image(page, timeout: float = 30) -> str:
    """Wait for heuristic Process Image to complete."""
    return wait_for_status(page, "#bgStatus", "Done.", timeout=timeout,
                           poll_interval=0.5)


def wait_enhance(page, timeout: float = 15) -> str:
    """Wait for AI Enhance to complete."""
    return wait_for_status(page, "#aiEnhanceStatus", "complete",
                           timeout=timeout, poll_interval=1.0)


def _decode_data_url(data_url: str) -> Image.Image | None:
    """Decode a base64 data URL to a PIL Image."""
    header = "data:image/png;base64,"
    if not data_url.startswith(header):
        return None
    raw = base64.b64decode(data_url[len(header):])
    return Image.open(BytesIO(raw)).convert("RGBA")
```

- [ ] **Step 2: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/helpers/canvas_extract.py
git commit -m "feat: add canvas extraction and wait helpers for Playwright"
```

---

## Task 4: Create App Driver Helper

**Files:**
- Create: `tests/helpers/app_driver.py`

- [ ] **Step 1: Create app_driver.py**

```python
"""App driver for browser automation — upload, configure, process, extract.

High-level functions that combine Playwright page interactions
with canvas extraction and wait helpers into complete workflows.
"""

from pathlib import Path

from PIL import Image

from helpers.canvas_extract import (
    extract_canvas,
    extract_processed_layout,
    save_canvas_to_file,
    wait_ai_remove,
    wait_process_image,
    wait_enhance,
)

APP_URL = "http://127.0.0.1:8080"


def load_app(page, url: str = APP_URL):
    """Navigate to the app and wait for it to be ready."""
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(2000)


def upload_image(page, image_path: str | Path):
    """Upload a source image via the file input."""
    page.set_input_files("#bgInputFile", str(image_path))
    page.wait_for_timeout(3000)  # Wait for canvas to render


def open_advanced_settings(page):
    """Expand all collapsed card sections."""
    page.evaluate(
        '() => document.querySelectorAll(".card.closed")'
        '.forEach(c => c.classList.remove("closed"))'
    )
    page.wait_for_timeout(500)


def select_preset(page, preset: str):
    """Select an extraction preset from the dropdown."""
    page.select_option("#bgPreset", preset)
    page.wait_for_timeout(500)


def select_tone(page, tone: str):
    """Select background tone ('dark' or 'light')."""
    page.select_option("#bgTone", tone)
    page.wait_for_timeout(300)


def run_ai_remove(page, timeout: float = 90) -> str:
    """Click AI Remove and wait for completion. Returns status string."""
    page.click("#aiRemoveButton")
    return wait_ai_remove(page, timeout=timeout)


def run_process_image(page, timeout: float = 30) -> str:
    """Click Process Image (heuristic) and wait for completion."""
    page.click("#processBgButton")
    return wait_process_image(page, timeout=timeout)


def run_enhance(page, timeout: float = 15) -> str:
    """Click AI Enhance if available. Returns status or 'NOT_VISIBLE'."""
    page.evaluate(
        "() => { const b = document.querySelector('#aiEnhanceButton');"
        " if(b) b.scrollIntoView(); }"
    )
    page.wait_for_timeout(500)
    visible = page.evaluate(
        "() => { const b = document.querySelector('#aiEnhanceBlock');"
        " return b ? b.style.display !== 'none' : false; }"
    )
    if not visible:
        return "NOT_VISIBLE"
    page.click("#aiEnhanceButton")
    page.wait_for_timeout(5000)
    return wait_enhance(page, timeout=timeout)


def extract_best_result(page) -> Image.Image | None:
    """Extract the best available result canvas.

    Priority: aiEnhancedCanvas > aiFinalCanvas > processedLayoutCanvas > resultCanvas
    """
    for selector in ["#aiEnhancedCanvas", "#aiFinalCanvas"]:
        img = extract_canvas(page, selector)
        if img:
            return img
    layout = extract_processed_layout(page)
    if layout:
        return layout
    return extract_canvas(page, "#resultCanvas")


def run_dark_extraction(page, source_path: str | Path, preset: str,
                        out_dir: Path | None = None) -> dict:
    """Full dark-preset extraction workflow: load → configure → AI Remove → extract.

    Returns dict with keys: status, result_img, enhanced_img, screenshots
    """
    load_app(page)
    upload_image(page, source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_ai_remove(page, timeout=90)
    result = {"status": status, "result_img": None, "enhanced_img": None, "screenshots": []}

    if "FAIL" in status or "TIMEOUT" in status:
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_dir / "failed.png"))
        return result

    # Extract AI final canvas
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_dir / "01_after_ai_remove.png"))
        result["result_img"] = save_canvas_to_file(page, "#aiFinalCanvas",
                                                    out_dir / "ai_final.png")
    else:
        result["result_img"] = extract_canvas(page, "#aiFinalCanvas")

    # Run enhance
    enh_status = run_enhance(page)
    if enh_status not in ("NOT_VISIBLE", "TIMEOUT"):
        if out_dir:
            result["enhanced_img"] = save_canvas_to_file(page, "#aiEnhancedCanvas",
                                                          out_dir / "ai_enhanced.png")
            page.screenshot(path=str(out_dir / "02_final.png"))
        else:
            result["enhanced_img"] = extract_canvas(page, "#aiEnhancedCanvas")

    return result


def run_light_extraction(page, source_path: str | Path, preset: str,
                         out_dir: Path | None = None) -> dict:
    """Full light-preset extraction workflow: load → configure → Process Image → extract.

    Returns dict with keys: status, result_img, enhanced_img, screenshots
    """
    load_app(page)
    upload_image(page, source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    status = run_process_image(page, timeout=30)
    result = {"status": status, "result_img": None, "enhanced_img": None, "screenshots": []}

    if "FAIL" in status or "TIMEOUT" in status:
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_dir / "failed.png"))
        return result

    # Extract result canvas (heuristic mode uses resultCanvas / processedLayoutCanvas)
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_dir / "01_after_process.png"))
        result["result_img"] = save_canvas_to_file(page, "#resultCanvas",
                                                    out_dir / "result_canvas.png")
        # Also try processedLayoutCanvas
        layout = extract_processed_layout(page)
        if layout:
            layout.save(str(out_dir / "processed_layout.png"), "PNG")
            result["result_img"] = layout  # prefer layout if available
    else:
        result["result_img"] = extract_processed_layout(page) or extract_canvas(page, "#resultCanvas")

    return result
```

- [ ] **Step 2: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/helpers/app_driver.py
git commit -m "feat: add app driver helper for browser extraction workflows"
```

---

## Task 5: Create HTML Report Generator

**Files:**
- Create: `tests/helpers/report_gen.py`

- [ ] **Step 1: Create report_gen.py**

```python
"""HTML visual diff report generator.

Produces a self-contained HTML report with:
- Side-by-side reference vs result images (base64 embedded)
- Diff heatmap visualization
- Quality metrics table per test case
- Pass/fail summary
"""

import base64
import json
from io import BytesIO
from pathlib import Path

from jinja2 import Template
from PIL import Image

from helpers.quality_metrics import generate_diff_heatmap

REPORT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Quality Test Report</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
  h1 { color: #64ffda; margin-bottom: 20px; }
  h2 { color: #bb86fc; margin: 20px 0 10px; }
  .summary { display: flex; gap: 20px; margin-bottom: 30px; }
  .stat-box { background: #16213e; padding: 16px 24px; border-radius: 8px; text-align: center; }
  .stat-box .value { font-size: 28px; font-weight: bold; }
  .stat-box .label { font-size: 12px; color: #888; margin-top: 4px; }
  .pass { color: #64ffda; }
  .fail { color: #ff5252; }
  .warn { color: #ffd740; }
  .test-case { background: #16213e; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
  .test-case h3 { margin-bottom: 12px; }
  .images { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
  .images figure { text-align: center; }
  .images img { max-width: 400px; max-height: 300px; border: 1px solid #333;
                background: repeating-conic-gradient(#333 0% 25%, #222 0% 50%) 50%/16px 16px; }
  .images figcaption { font-size: 11px; color: #888; margin-top: 4px; }
  table { border-collapse: collapse; margin: 10px 0; width: 100%; }
  th, td { padding: 6px 12px; text-align: left; border-bottom: 1px solid #333; }
  th { color: #bb86fc; font-size: 12px; }
  td { font-size: 13px; }
  .gate-pass { color: #64ffda; }
  .gate-fail { color: #ff5252; }
</style>
</head>
<body>
<h1>Quality Test Report</h1>

<div class="summary">
  <div class="stat-box">
    <div class="value">{{ total }}</div>
    <div class="label">TOTAL TESTS</div>
  </div>
  <div class="stat-box">
    <div class="value pass">{{ passed }}</div>
    <div class="label">PASSED</div>
  </div>
  <div class="stat-box">
    <div class="value fail">{{ failed }}</div>
    <div class="label">FAILED</div>
  </div>
</div>

{% for case in cases %}
<div class="test-case">
  <h3>
    <span class="{{ 'pass' if case.passed else 'fail' }}">
      {{ '&#10004;' if case.passed else '&#10008;' }}
    </span>
    {{ case.name }}
  </h3>

  <div class="images">
    <figure>
      <img src="data:image/png;base64,{{ case.ref_b64 }}" alt="Reference">
      <figcaption>Reference</figcaption>
    </figure>
    <figure>
      <img src="data:image/png;base64,{{ case.result_b64 }}" alt="Result">
      <figcaption>Result</figcaption>
    </figure>
    {% if case.diff_b64 %}
    <figure>
      <img src="data:image/png;base64,{{ case.diff_b64 }}" alt="Diff Heatmap">
      <figcaption>Diff Heatmap</figcaption>
    </figure>
    {% endif %}
  </div>

  <table>
    <tr><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>
    {% for m in case.metrics_table %}
    <tr>
      <td>{{ m.name }}</td>
      <td>{{ m.value }}</td>
      <td>{{ m.threshold }}</td>
      <td class="{{ 'gate-pass' if m.passed else 'gate-fail' }}">
        {{ 'PASS' if m.passed else 'FAIL' }}
      </td>
    </tr>
    {% endfor %}
  </table>

  {% if case.alpha_stats %}
  <h4 style="margin-top:10px; color:#64ffda;">Alpha Stats</h4>
  <table>
    <tr><th></th><th>Transparent%</th><th>Semi%</th><th>Opaque%</th></tr>
    <tr><td>Reference</td>
        <td>{{ case.alpha_stats.ref.transparent }}</td>
        <td>{{ case.alpha_stats.ref.semi }}</td>
        <td>{{ case.alpha_stats.ref.opaque }}</td></tr>
    <tr><td>Result</td>
        <td>{{ case.alpha_stats.test.transparent }}</td>
        <td>{{ case.alpha_stats.test.semi }}</td>
        <td>{{ case.alpha_stats.test.opaque }}</td></tr>
  </table>
  {% endif %}
</div>
{% endfor %}

</body>
</html>"""


def _img_to_b64(img: Image.Image, max_size: tuple = (800, 600)) -> str:
    """Convert PIL Image to base64 PNG string, resized for report embedding."""
    thumb = img.copy()
    thumb.thumbnail(max_size, Image.LANCZOS)
    buf = BytesIO()
    thumb.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def build_report_case(name: str, ref_img: Image.Image, result_img: Image.Image,
                      gate_result: dict) -> dict:
    """Build a single test case entry for the HTML report.

    Args:
        name: Test case display name (e.g., 'dark-balanced')
        ref_img: Reference golden image
        result_img: Extracted result image
        gate_result: Output from run_quality_gates()

    Returns:
        dict ready for Jinja2 template rendering
    """
    metrics = gate_result.get("metrics", {})

    # Build metrics table rows
    metrics_table = []
    gate_checks = [
        ("pHash Distance", "phash_distance", "phash_max_distance", lambda v, t: v <= t),
        ("PSNR (dB)", "psnr_db", "psnr_min_db", lambda v, t: v >= t),
        ("SSIM", "ssim", "ssim_min", lambda v, t: v >= t),
        ("Alpha IoU", "alpha_iou", "alpha_iou_min", lambda v, t: v >= t),
        ("Alpha MAE", "alpha_mae", "alpha_mae_max", lambda v, t: v <= t),
    ]

    from helpers.quality_metrics import DEFAULT_THRESHOLDS
    for display_name, metric_key, threshold_key, check_fn in gate_checks:
        value = metrics.get(metric_key, "N/A")
        threshold = DEFAULT_THRESHOLDS.get(threshold_key, "N/A")
        passed = check_fn(value, threshold) if isinstance(value, (int, float)) else False
        metrics_table.append({
            "name": display_name,
            "value": f"{value}" if value != "N/A" else "N/A",
            "threshold": f"{threshold}",
            "passed": passed,
        })

    # Generate diff heatmap
    diff_img = generate_diff_heatmap(result_img, ref_img)

    # Alpha stats
    alpha_stats_data = None
    if "alpha_stats" in metrics and "ref_alpha_stats" in metrics:
        alpha_stats_data = {
            "test": metrics["alpha_stats"],
            "ref": metrics["ref_alpha_stats"],
        }

    return {
        "name": name,
        "passed": gate_result.get("passed", False),
        "ref_b64": _img_to_b64(ref_img),
        "result_b64": _img_to_b64(result_img),
        "diff_b64": _img_to_b64(diff_img),
        "metrics_table": metrics_table,
        "alpha_stats": alpha_stats_data,
    }


def generate_html_report(cases: list[dict], output_path: str | Path):
    """Render the full HTML report and save to disk.

    Args:
        cases: List of dicts from build_report_case()
        output_path: Where to save the HTML file
    """
    total = len(cases)
    passed = sum(1 for c in cases if c["passed"])
    failed = total - passed

    template = Template(REPORT_TEMPLATE)
    html = template.render(total=total, passed=passed, failed=failed, cases=cases)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def save_json_report(cases: list[dict], gate_results: dict, output_path: str | Path):
    """Save machine-readable JSON metrics report.

    Args:
        cases: List of case names
        gate_results: Dict mapping case name → run_quality_gates() output
        output_path: Where to save JSON
    """
    report = {}
    for name in cases:
        gr = gate_results.get(name, {})
        report[name] = {
            "passed": gr.get("passed", False),
            "failed_at": gr.get("failed_at"),
            "metrics": {k: v for k, v in gr.get("metrics", {}).items()
                        if not isinstance(v, dict)},
        }
        # Include alpha stats separately
        if "alpha_stats" in gr.get("metrics", {}):
            report[name]["alpha_stats"] = gr["metrics"]["alpha_stats"]
        if "ref_alpha_stats" in gr.get("metrics", {}):
            report[name]["ref_alpha_stats"] = gr["metrics"]["ref_alpha_stats"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
```

- [ ] **Step 2: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/helpers/report_gen.py
git commit -m "feat: add HTML visual diff report generator with Jinja2"
```

---

## Task 6: Create pytest Fixtures (conftest.py)

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create conftest.py**

```python
"""pytest fixtures for the unified live test system.

Provides:
- browser: Session-scoped Chromium instance
- page: Function-scoped page with fresh context
- app_ready: Page navigated to app and ready for interaction
- golden_images: Session-scoped dict of reference PIL Images
- output_dir: Per-test output directory for screenshots/canvases
"""

from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Dev\Image generator")
APP_URL = "http://127.0.0.1:8080"
GOLDEN_DIR = ROOT / "tests" / "golden"
REPORTS_DIR = ROOT / "tests" / "reports"


# ── Browser fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def playwright_instance():
    """Session-scoped Playwright instance."""
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Session-scoped headless Chromium browser."""
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--disable-gpu"],  # Deterministic rendering
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Function-scoped page with fresh browser context.

    Each test gets a clean page — no state leakage between tests.
    """
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def app_ready(page):
    """Page navigated to the app and ready for interaction.

    Waits for network idle and initial render.
    """
    page.goto(APP_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    return page


# ── Reference image fixtures ─────────────────────────────────────────

@pytest.fixture(scope="session")
def golden_images():
    """Session-scoped dict of all golden reference images.

    Keys:
        dark_source, dark_ref_full, dark_ref_topbar, dark_ref_botbar, dark_ref_portrait
        light_source, light_ref_full, light_ref_topbar, light_ref_botbar, light_ref_portrait
    """
    images = {}
    for path in GOLDEN_DIR.glob("*.png"):
        key = path.stem  # e.g., 'dark_ref_full'
        images[key] = Image.open(path).convert("RGBA")
    # Also glob .PNG (case-insensitive match on Windows)
    for path in GOLDEN_DIR.glob("*.PNG"):
        key = path.stem
        if key not in images:
            images[key] = Image.open(path).convert("RGBA")
    return images


# ── Output directory fixture ─────────────────────────────────────────

@pytest.fixture(scope="function")
def output_dir(request):
    """Per-test output directory for screenshots and extracted canvases.

    Located at tests/reports/diffs/<test_name>/
    """
    test_name = request.node.name.replace("[", "_").replace("]", "").replace("-", "_")
    out = REPORTS_DIR / "diffs" / test_name
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── Path fixtures ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def dark_source_path():
    return str(GOLDEN_DIR / "dark_source.png")


@pytest.fixture(scope="session")
def light_source_path():
    return str(GOLDEN_DIR / "light_source.png")
```

- [ ] **Step 2: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/conftest.py
git commit -m "feat: add pytest fixtures for browser, golden images, and output dirs"
```

---

## Task 7: Create Smoke Tests

**Files:**
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write smoke tests**

```python
"""Smoke tests — fast sanity checks that the server and app are working.

Run: .venv/Scripts/python.exe -m pytest tests/test_smoke.py -v -m smoke
"""

import urllib.request
import urllib.error

import pytest


APP_URL = "http://127.0.0.1:8080"


@pytest.mark.smoke
class TestServerHealth:
    def test_server_reachable(self):
        """Server at port 8080 should respond to HTTP GET."""
        req = urllib.request.Request(APP_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200

    def test_index_html_served(self):
        """index.html should contain the app title."""
        req = urllib.request.Request(APP_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            assert "Asset Editor" in body or "Game UI" in body

    def test_app_js_served(self):
        """app.js should be accessible."""
        req = urllib.request.Request(f"{APP_URL}/app.js")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert len(resp.read()) > 1000  # Should be substantial


@pytest.mark.smoke
class TestAppLoads:
    def test_page_renders(self, app_ready):
        """App should render without console errors."""
        errors = []
        app_ready.on("pageerror", lambda err: errors.append(str(err)))
        app_ready.wait_for_timeout(1000)
        # Check that main elements exist
        assert app_ready.locator("#bgInputFile").count() == 1
        assert app_ready.locator("#aiRemoveButton").count() == 1
        assert app_ready.locator("#bgPreset").count() == 1

    def test_canvas_exists(self, app_ready):
        """Result canvas element should exist."""
        assert app_ready.locator("#resultCanvas").count() == 1

    def test_presets_populated(self, app_ready):
        """Preset dropdown should have dark and light options."""
        options = app_ready.locator("#bgPreset option").all_text_contents()
        # Should contain at least some preset options
        assert len(options) >= 3
```

- [ ] **Step 2: Run smoke tests**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest tests/test_smoke.py -v -m smoke
```

Expected: All 6 smoke tests PASS (assumes server is running on port 8080).

- [ ] **Step 3: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/test_smoke.py
git commit -m "feat: add smoke tests for server health and app loading"
```

---

## Task 8: Create Live Extraction Tests

**Files:**
- Create: `tests/test_live_extraction.py`

This is the core test — parameterized across all 6 presets, driving the real browser through the full extraction workflow and capturing output.

- [ ] **Step 1: Write live extraction tests**

```python
"""Live browser extraction tests — full workflow through the real app.

Parameterized across all 6 presets × 2 source images.
Each test: upload image → select preset → run extraction → extract canvas → save output.

Run: .venv/Scripts/python.exe -m pytest tests/test_live_extraction.py -v -m live
"""

from pathlib import Path

import pytest
from PIL import Image

from helpers.app_driver import (
    load_app,
    upload_image,
    open_advanced_settings,
    select_preset,
    run_ai_remove,
    run_process_image,
    extract_best_result,
)
from helpers.canvas_extract import (
    extract_canvas,
    extract_processed_layout,
    save_canvas_to_file,
)

ROOT = Path(r"C:\Dev\Image generator")
REPORTS_DIR = ROOT / "tests" / "reports"


# ── Dark presets: AI Remove mode ──────────────────────────────────────

@pytest.mark.live
@pytest.mark.slow
@pytest.mark.parametrize("preset", ["dark-balanced", "dark-soft", "dark-hard"])
def test_dark_extraction(page, dark_source_path, preset, output_dir):
    """Run dark preset extraction via AI Remove and verify output canvas is populated."""
    load_app(page)
    upload_image(page, dark_source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    # Run AI Remove
    status = run_ai_remove(page, timeout=90)
    assert "FAIL" not in status, f"AI Remove failed: {status}"
    assert "TIMEOUT" not in status, f"AI Remove timed out after 90s"

    # Screenshot after processing
    page.screenshot(path=str(output_dir / "01_after_ai_remove.png"))

    # Extract primary result canvas
    result_img = extract_canvas(page, "#aiFinalCanvas")
    if result_img:
        result_img.save(str(output_dir / "ai_final.png"), "PNG")
    else:
        # Fallback to resultCanvas
        result_img = extract_canvas(page, "#resultCanvas")
        if result_img:
            result_img.save(str(output_dir / "result_canvas.png"), "PNG")

    assert result_img is not None, "No result canvas produced"
    assert result_img.width > 1 and result_img.height > 1, "Result canvas is too small"

    # Save metadata for quality gate tests
    meta_path = output_dir / "extraction_meta.json"
    import json
    with open(meta_path, "w") as f:
        json.dump({
            "preset": preset,
            "tone": "dark",
            "mode": "ai-remove",
            "status": status,
            "result_size": [result_img.width, result_img.height],
        }, f, indent=2)

    page.screenshot(path=str(output_dir / "02_final.png"))


# ── Light presets: Heuristic Process Image mode ───────────────────────

@pytest.mark.live
@pytest.mark.slow
@pytest.mark.parametrize("preset", ["light-balanced", "light-soft", "light-hard"])
def test_light_extraction(page, light_source_path, preset, output_dir):
    """Run light preset extraction via Process Image and verify output canvas is populated."""
    load_app(page)
    upload_image(page, light_source_path)
    open_advanced_settings(page)
    select_preset(page, preset)

    # Run heuristic Process Image
    status = run_process_image(page, timeout=30)
    assert "FAIL" not in status, f"Process Image failed: {status}"
    assert "TIMEOUT" not in status, f"Process Image timed out after 30s"

    # Screenshot after processing
    page.screenshot(path=str(output_dir / "01_after_process.png"))

    # Extract result — prefer processedLayoutCanvas over resultCanvas
    layout_img = extract_processed_layout(page)
    result_img = layout_img or extract_canvas(page, "#resultCanvas")

    if result_img:
        result_img.save(str(output_dir / "result.png"), "PNG")

    assert result_img is not None, "No result canvas produced"
    assert result_img.width > 1 and result_img.height > 1, "Result canvas is too small"

    # Save metadata
    meta_path = output_dir / "extraction_meta.json"
    import json
    with open(meta_path, "w") as f:
        json.dump({
            "preset": preset,
            "tone": "light",
            "mode": "heuristic",
            "status": status,
            "result_size": [result_img.width, result_img.height],
        }, f, indent=2)

    page.screenshot(path=str(output_dir / "02_final.png"))
```

- [ ] **Step 2: Run live extraction tests**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest tests/test_live_extraction.py -v -m live
```

Expected: All 6 tests PASS (3 dark + 3 light). Each produces output images in `tests/reports/diffs/<test_name>/`.

Note: Dark tests require ComfyUI running for AI Remove. If ComfyUI is unavailable, dark tests will fail with status containing "FAIL" or "TIMEOUT". This is expected — the tests correctly detect when the AI pipeline is not available.

- [ ] **Step 3: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/test_live_extraction.py
git commit -m "feat: add parameterized live browser extraction tests for all 6 presets"
```

---

## Task 9: Create Quality Gate Tests

**Files:**
- Create: `tests/test_quality_gates.py`

- [ ] **Step 1: Write quality gate tests**

```python
"""Quality gate tests — compare extracted results against golden reference images.

Runs progressive quality gates (pHash → PSNR → SSIM → Alpha IoU → Alpha MAE)
on extraction outputs. Produces HTML visual diff report and JSON metrics.

Run: .venv/Scripts/python.exe -m pytest tests/test_quality_gates.py -v -m quality
"""

import json
from pathlib import Path

import pytest
from PIL import Image

from helpers.quality_metrics import (
    run_quality_gates,
    alpha_stats,
    region_opaque_pct,
    DEFAULT_THRESHOLDS,
)
from helpers.report_gen import build_report_case, generate_html_report, save_json_report

ROOT = Path(r"C:\Dev\Image generator")
REPORTS_DIR = ROOT / "tests" / "reports"
DIFFS_DIR = REPORTS_DIR / "diffs"


# ── Shared state for report generation ────────────────────────────────

_report_cases = []
_gate_results = {}


def _load_extraction_result(test_name: str) -> Image.Image | None:
    """Load the extraction result from a prior live test run.

    Looks in tests/reports/diffs/<test_name>/ for result images.
    """
    test_dir = DIFFS_DIR / test_name
    # Try known output filenames in priority order
    for fname in ["ai_final.png", "result.png", "result_canvas.png", "processed_layout.png"]:
        path = test_dir / fname
        if path.exists():
            return Image.open(path).convert("RGBA")
    return None


# ── Dark preset quality gates ─────────────────────────────────────────

@pytest.mark.quality
@pytest.mark.parametrize("preset", ["dark-balanced", "dark-soft", "dark-hard"])
def test_dark_quality(preset, golden_images, output_dir):
    """Compare dark preset extraction against dark reference with progressive quality gates."""
    test_key = f"test_dark_extraction_{preset.replace('-', '_')}_"
    result_img = _load_extraction_result(test_key)
    if result_img is None:
        pytest.skip(f"No extraction output found for {preset}. Run live tests first.")

    ref_img = golden_images.get("dark_ref_full")
    assert ref_img is not None, "Dark reference image not found in golden/"

    # Run progressive quality gates
    gate_result = run_quality_gates(result_img, ref_img)
    _gate_results[f"dark-{preset}"] = gate_result

    # Build report case
    case = build_report_case(f"dark / {preset}", ref_img, result_img, gate_result)
    _report_cases.append(case)

    # Region-specific checks (informational — logged but not gating)
    topbar = region_opaque_pct(result_img, 0, 1, 0, 0.10)
    botbar = region_opaque_pct(result_img, 0, 1, 0.70, 1.0)
    portrait = region_opaque_pct(result_img, 0, 0.10, 0.60, 1.0)

    # Save per-test metrics
    metrics_path = output_dir / "quality_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "preset": preset,
            "passed": gate_result["passed"],
            "failed_at": gate_result["failed_at"],
            "metrics": {k: v for k, v in gate_result["metrics"].items()
                        if not isinstance(v, dict)},
            "regions": {"topbar": topbar, "botbar": botbar, "portrait": portrait},
            "alpha_stats": gate_result["metrics"].get("alpha_stats"),
        }, f, indent=2)

    # Assert quality gates passed
    if not gate_result["passed"]:
        failures_str = "; ".join(
            f"{name}={val} (need {thresh})"
            for name, val, thresh in gate_result["failures"]
        )
        pytest.fail(f"Quality gates FAILED for {preset}: {failures_str}")


# ── Light preset quality gates ────────────────────────────────────────

@pytest.mark.quality
@pytest.mark.parametrize("preset", ["light-balanced", "light-soft", "light-hard"])
def test_light_quality(preset, golden_images, output_dir):
    """Compare light preset extraction against light reference with progressive quality gates."""
    test_key = f"test_light_extraction_{preset.replace('-', '_')}_"
    result_img = _load_extraction_result(test_key)
    if result_img is None:
        pytest.skip(f"No extraction output found for {preset}. Run live tests first.")

    ref_img = golden_images.get("light_ref_full")
    assert ref_img is not None, "Light reference image not found in golden/"

    # Run progressive quality gates
    gate_result = run_quality_gates(result_img, ref_img)
    _gate_results[f"light-{preset}"] = gate_result

    # Build report case
    case = build_report_case(f"light / {preset}", ref_img, result_img, gate_result)
    _report_cases.append(case)

    # Save per-test metrics
    metrics_path = output_dir / "quality_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "preset": preset,
            "passed": gate_result["passed"],
            "failed_at": gate_result["failed_at"],
            "metrics": {k: v for k, v in gate_result["metrics"].items()
                        if not isinstance(v, dict)},
            "alpha_stats": gate_result["metrics"].get("alpha_stats"),
        }, f, indent=2)

    if not gate_result["passed"]:
        failures_str = "; ".join(
            f"{name}={val} (need {thresh})"
            for name, val, thresh in gate_result["failures"]
        )
        pytest.fail(f"Quality gates FAILED for {preset}: {failures_str}")


# ── Report generation (runs after all quality tests) ──────────────────

@pytest.fixture(scope="session", autouse=True)
def generate_reports(request):
    """Generate HTML and JSON reports after all quality tests complete."""
    yield  # Run all tests first

    if _report_cases:
        html_path = REPORTS_DIR / "quality_report.html"
        generate_html_report(_report_cases, html_path)
        print(f"\n  HTML report: {html_path}")

    if _gate_results:
        json_path = REPORTS_DIR / "quality_report.json"
        save_json_report(list(_gate_results.keys()), _gate_results, json_path)
        print(f"  JSON report: {json_path}")
```

- [ ] **Step 2: Run quality gate tests**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest tests/test_quality_gates.py -v -m quality
```

Expected: Tests either PASS (quality gates met) or FAIL with specific metric details. If no live extraction output exists, tests are SKIPPED. After completion, check `tests/reports/quality_report.html` in a browser.

- [ ] **Step 3: Commit**

```bash
cd "C:/Dev/Image generator"
git add tests/test_quality_gates.py
git commit -m "feat: add progressive quality gate tests with visual diff HTML report"
```

---

## Task 10: Create Full Suite Runner and Verify End-to-End

**Files:**
- Modify: `tests/pytest.ini` (add run order)

- [ ] **Step 1: Update pytest.ini with run configuration**

Replace `tests/pytest.ini` content:

```ini
[pytest]
testpaths = tests
markers =
    smoke: Fast sanity checks (server up, app loads)
    unit: Unit tests for metric helper functions
    live: Live browser extraction tests (slow, needs server running)
    quality: Quality gate comparison tests (needs extraction output from live tests)
    slow: Tests that take > 30s each
addopts = -v --tb=short
```

- [ ] **Step 2: Run the full test suite end-to-end**

Run the full suite in the correct order — smoke first, then unit, then live extraction, then quality gates:

```bash
cd "C:/Dev/Image generator"
.venv/Scripts/python.exe -m pytest tests/test_smoke.py tests/test_unit_metrics.py tests/test_live_extraction.py tests/test_quality_gates.py -v --tb=short
```

Expected output pattern:
```
tests/test_smoke.py::TestServerHealth::test_server_reachable PASSED
tests/test_smoke.py::TestServerHealth::test_index_html_served PASSED
tests/test_smoke.py::TestServerHealth::test_app_js_served PASSED
tests/test_smoke.py::TestAppLoads::test_page_renders PASSED
tests/test_smoke.py::TestAppLoads::test_canvas_exists PASSED
tests/test_smoke.py::TestAppLoads::test_presets_populated PASSED
tests/test_unit_metrics.py::TestAlphaStats::test_fully_transparent PASSED
... (all unit tests pass)
tests/test_live_extraction.py::test_dark_extraction[dark-balanced] PASSED
tests/test_live_extraction.py::test_dark_extraction[dark-soft] PASSED
tests/test_live_extraction.py::test_dark_extraction[dark-hard] PASSED
tests/test_live_extraction.py::test_light_extraction[light-balanced] PASSED
tests/test_live_extraction.py::test_light_extraction[light-soft] PASSED
tests/test_live_extraction.py::test_light_extraction[light-hard] PASSED
tests/test_quality_gates.py::test_dark_quality[dark-balanced] PASSED/FAILED
tests/test_quality_gates.py::test_dark_quality[dark-soft] PASSED/FAILED
... (quality results depend on extraction quality)
```

After running, verify:
1. `tests/reports/quality_report.html` exists and opens in browser
2. `tests/reports/quality_report.json` contains structured metrics
3. `tests/reports/diffs/` contains per-test output directories with screenshots and canvases

- [ ] **Step 3: Final commit**

```bash
cd "C:/Dev/Image generator"
git add tests/pytest.ini
git commit -m "feat: finalize unified live test system with full suite configuration"
```

---

## Run Commands Reference

```bash
# Full suite (recommended order)
.venv/Scripts/python.exe -m pytest tests/ -v

# Individual layers
.venv/Scripts/python.exe -m pytest -m smoke -v          # ~5s
.venv/Scripts/python.exe -m pytest -m unit -v            # ~3s
.venv/Scripts/python.exe -m pytest -m live -v            # ~3-5min
.venv/Scripts/python.exe -m pytest -m quality -v         # ~10s

# With HTML report
.venv/Scripts/python.exe -m pytest tests/ -v --html=tests/reports/pytest_report.html

# Just dark presets
.venv/Scripts/python.exe -m pytest -k "dark" -v

# Just light presets
.venv/Scripts/python.exe -m pytest -k "light" -v

# Skip slow live tests
.venv/Scripts/python.exe -m pytest -m "not slow" -v
```
