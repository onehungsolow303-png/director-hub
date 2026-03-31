# Multi-Spectrum Border Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dual-criteria border detection with a 40-technique multi-spectrum ensemble that runs Python-side on every image the app processes, with self-calibrating weights learned from test runs.

**Architecture:** Python package `border_detect/` with 9 technique modules, ensemble combiner, calibration engine, and API endpoint at `/api/border-detect`. Browser-side `app.js` calls the endpoint before building the mask, falling back to current v5+ detection if the server is unavailable.

**Tech Stack:** Python 3.12, opencv-python, scikit-image, numpy, scipy, PyWavelets, concurrent.futures

**Spec:** `docs/superpowers/specs/2026-03-30-multi-spectrum-border-detection-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| **Create:** `border_detect/__init__.py` | Package init, exports `detect_borders()` |
| **Create:** `border_detect/preprocess.py` | Shared image conversions (grayscale, HSV, LAB, YCbCr, integral images) |
| **Create:** `border_detect/techniques/__init__.py` | Technique registry — discover and run all techniques |
| **Create:** `border_detect/techniques/edge.py` | 8 edge detection techniques |
| **Create:** `border_detect/techniques/color.py` | 5 color-space analysis techniques |
| **Create:** `border_detect/techniques/morphological.py` | 5 morphological operations |
| **Create:** `border_detect/techniques/texture.py` | 4 texture analysis techniques |
| **Create:** `border_detect/techniques/statistical.py` | 4 statistical methods |
| **Create:** `border_detect/techniques/gradient.py` | 3 gradient analysis techniques |
| **Create:** `border_detect/techniques/structural.py` | 4 structural analysis techniques |
| **Create:** `border_detect/techniques/adaptive.py` | 4 adaptive & frequency techniques |
| **Create:** `border_detect/techniques/quantization.py` | 3 color quantization & grouping techniques |
| **Create:** `border_detect/ensemble.py` | Weighted voting + consensus combiner |
| **Create:** `border_detect/calibrate.py` | Score techniques, update weights JSON |
| **Create:** `api/endpoints/border_detect.py` | `/api/border-detect` endpoint handler |
| **Create:** `.claude/skills/border-detect/SKILL.md` | Diagnostic skill definition |
| **Create:** `tests/test_border_detect.py` | Unit + integration tests |
| **Modify:** `serve.py:221-247` | Register border_detect endpoint |
| **Modify:** `app.js:2380-2400` | Call `/api/border-detect` before v5+ fallback |

---

### Task 1: Install dependencies and create package skeleton

**Files:**
- Create: `border_detect/__init__.py`
- Create: `border_detect/preprocess.py`
- Create: `border_detect/techniques/__init__.py`

- [ ] **Step 1: Install Python dependencies**

Run:
```bash
cd "C:/Dev/Image generator"
.venv/Scripts/pip.exe install opencv-python scikit-image PyWavelets
```

Expected: Successfully installed opencv-python, scikit-image, PyWavelets (numpy/scipy already present).

- [ ] **Step 2: Verify imports work**

Run:
```bash
.venv/Scripts/python.exe -c "import cv2; import skimage; import pywt; print(f'cv2={cv2.__version__}, skimage={skimage.__version__}, pywt={pywt.__version__}')"
```

Expected: Version strings printed, no errors.

- [ ] **Step 3: Write the failing test**

Create `tests/test_border_detect.py`:

```python
"""Tests for the multi-spectrum border detection package."""

import numpy as np
import pytest


def test_preprocess_creates_all_colorspaces():
    """preprocess() should return grayscale, HSV, LAB, YCbCr, and integral images."""
    from border_detect.preprocess import preprocess
    # 10x10 random RGB image
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
    # Each technique is a (id, callable) tuple
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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'border_detect'`

- [ ] **Step 5: Create package skeleton**

Create `border_detect/__init__.py`:

```python
"""Multi-spectrum border detection — 40-technique ensemble with self-calibrating weights."""

from border_detect.ensemble import detect_borders

__all__ = ["detect_borders"]
```

Create `border_detect/preprocess.py`:

```python
"""Shared image preprocessing — convert once, reuse across all techniques."""

import cv2
import numpy as np


def preprocess(img_bgr):
    """Convert source image into all needed representations.

    Args:
        img_bgr: numpy array (H, W, 3) in BGR format (opencv default)
                 or RGB format — caller must specify.

    Returns:
        dict with keys: gray, hsv, lab, ycbcr, integral, integral_sq, bgr, rgb
    """
    if img_bgr.ndim != 3 or img_bgr.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) image, got {img_bgr.shape}")

    bgr = img_bgr
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    ycbcr = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)

    # Integral images for fast windowed statistics
    gray_f = gray.astype(np.float64)
    integral = cv2.integral(gray_f)
    integral_sq = cv2.integral(gray_f * gray_f)

    return {
        "bgr": bgr,
        "rgb": rgb,
        "gray": gray,
        "hsv": hsv,
        "lab": lab,
        "ycbcr": ycbcr,
        "integral": integral,
        "integral_sq": integral_sq,
        "height": bgr.shape[0],
        "width": bgr.shape[1],
    }
```

Create `border_detect/techniques/__init__.py`:

```python
"""Technique registry — discovers and runs all border detection techniques."""

from border_detect.techniques.edge import TECHNIQUES as EDGE
from border_detect.techniques.color import TECHNIQUES as COLOR
from border_detect.techniques.morphological import TECHNIQUES as MORPHOLOGICAL
from border_detect.techniques.texture import TECHNIQUES as TEXTURE
from border_detect.techniques.statistical import TECHNIQUES as STATISTICAL
from border_detect.techniques.gradient import TECHNIQUES as GRADIENT
from border_detect.techniques.structural import TECHNIQUES as STRUCTURAL
from border_detect.techniques.adaptive import TECHNIQUES as ADAPTIVE
from border_detect.techniques.quantization import TECHNIQUES as QUANTIZATION


def get_all_techniques():
    """Return list of (technique_id, callable) tuples for all 40 techniques.

    Each callable has signature: fn(preprocessed: dict) -> np.ndarray (H, W) float32 0.0-1.0
    """
    all_techniques = []
    for module_techniques in [EDGE, COLOR, MORPHOLOGICAL, TEXTURE, STATISTICAL,
                              GRADIENT, STRUCTURAL, ADAPTIVE, QUANTIZATION]:
        all_techniques.extend(module_techniques)
    return all_techniques
```

- [ ] **Step 6: Create stub technique modules (all 9)**

Each technique module needs a `TECHNIQUES` list for the registry to import. Create stubs that will be filled in Tasks 3-11.

Create `border_detect/techniques/edge.py`:
```python
"""Edge detection techniques (8)."""

import cv2
import numpy as np


def _stub(preprocessed):
    """Placeholder — returns zeros."""
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


# Each entry: (technique_id, callable)
# callable signature: fn(preprocessed: dict) -> np.ndarray (H, W) float32 0.0-1.0
TECHNIQUES = [
    ("edge_sobel", _stub),
    ("edge_scharr", _stub),
    ("edge_prewitt", _stub),
    ("edge_roberts", _stub),
    ("edge_log", _stub),
    ("edge_dog", _stub),
    ("edge_canny", _stub),
    ("edge_phase", _stub),
]
```

Create `border_detect/techniques/color.py`:
```python
"""Color-space analysis techniques (5)."""

import cv2
import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("color_hsv_dark", _stub),
    ("color_lab_delta", _stub),
    ("color_ycbcr_luma", _stub),
    ("color_rgb_gradient", _stub),
    ("color_achromatic", _stub),
]
```

Create `border_detect/techniques/morphological.py`:
```python
"""Morphological operation techniques (5)."""

import cv2
import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("morph_gradient", _stub),
    ("morph_blackhat", _stub),
    ("morph_close_gaps", _stub),
    ("morph_tophat", _stub),
    ("morph_width_probe", _stub),
]
```

Create `border_detect/techniques/texture.py`:
```python
"""Texture analysis techniques (4)."""

import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("tex_lbp", _stub),
    ("tex_gabor", _stub),
    ("tex_glcm", _stub),
    ("tex_laws", _stub),
]
```

Create `border_detect/techniques/statistical.py`:
```python
"""Statistical method techniques (4)."""

import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("stat_variance", _stub),
    ("stat_entropy", _stub),
    ("stat_mahalanobis", _stub),
    ("stat_mean_diff", _stub),
]
```

Create `border_detect/techniques/gradient.py`:
```python
"""Gradient analysis techniques (3)."""

import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("grad_structure", _stub),
    ("grad_harris", _stub),
    ("grad_hog", _stub),
]
```

Create `border_detect/techniques/structural.py`:
```python
"""Structural analysis techniques (4)."""

import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("struct_contour", _stub),
    ("struct_ccl", _stub),
    ("struct_distance", _stub),
    ("struct_watershed", _stub),
]
```

Create `border_detect/techniques/adaptive.py`:
```python
"""Adaptive thresholding & frequency domain techniques (4)."""

import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("adapt_sauvola", _stub),
    ("adapt_niblack", _stub),
    ("freq_fft_highpass", _stub),
    ("freq_wavelet", _stub),
]
```

Create `border_detect/techniques/quantization.py`:
```python
"""Color quantization & grouping techniques (3)."""

import numpy as np


def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)


TECHNIQUES = [
    ("quant_median", _stub),
    ("quant_kmeans", _stub),
    ("quant_slic", _stub),
]
```

- [ ] **Step 7: Create stub ensemble.py**

Create `border_detect/ensemble.py`:

```python
"""Ensemble combiner — weighted voting + consensus for border detection."""

import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from border_detect.preprocess import preprocess
from border_detect.techniques import get_all_techniques


def detect_borders(img_bgr, mode="general", calibration_weights=None):
    """Run all 40 techniques and combine into a single border confidence map.

    Args:
        img_bgr: numpy array (H, W, 3) in BGR format.
        mode: "general" (A+C) or "test" (D).
        calibration_weights: dict of {technique_id: weight} or None for equal weights.

    Returns:
        dict with keys:
            border_map: np.ndarray (H, W) uint8 0-255
            techniques_run: int
            processing_ms: float
            consensus_count: int (max techniques agreeing on any pixel)
            per_technique: dict of {id: np.ndarray} (only in test mode)
    """
    start = time.time()
    preprocessed = preprocess(img_bgr)
    techniques = get_all_techniques()
    h, w = preprocessed["height"], preprocessed["width"]

    # Run all techniques in parallel
    results = {}
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(_run_one, tid, fn, preprocessed): tid
                   for tid, fn in techniques}
        for future in futures:
            tid = futures[future]
            try:
                results[tid] = future.result(timeout=10)
            except Exception as e:
                print(f"  Technique {tid} failed: {e}")
                results[tid] = np.zeros((h, w), dtype=np.float32)

    # Load weights
    if calibration_weights is None:
        calibration_weights = {}
    default_weight = 1.0 / len(techniques)
    weights = {tid: calibration_weights.get(tid, default_weight) for tid, _ in techniques}

    # Weighted ensemble
    weighted_sum = np.zeros((h, w), dtype=np.float64)
    weight_total = 0.0
    for tid, output in results.items():
        wt = weights[tid]
        weighted_sum += wt * output.astype(np.float64)
        weight_total += wt
    if weight_total > 0:
        weighted_map = weighted_sum / weight_total
    else:
        weighted_map = np.zeros((h, w), dtype=np.float64)

    # Consensus map
    consensus = np.zeros((h, w), dtype=np.int32)
    for output in results.values():
        consensus += (output > 0.5).astype(np.int32)
    consensus_threshold = max(1, len(techniques) // 4)  # 25% agreement
    consensus_mask = (consensus >= consensus_threshold).astype(np.float64)

    # Final: max of weighted ensemble and consensus mask
    final = np.maximum(weighted_map, consensus_mask)
    final_uint8 = np.clip(final * 255, 0, 255).astype(np.uint8)

    elapsed_ms = (time.time() - start) * 1000

    result = {
        "border_map": final_uint8,
        "techniques_run": len(results),
        "processing_ms": round(elapsed_ms, 1),
        "consensus_count": int(consensus.max()),
    }

    if mode == "test":
        result["per_technique"] = results

    return result


def _run_one(tid, fn, preprocessed):
    """Run a single technique safely."""
    output = fn(preprocessed)
    # Ensure output is float32 0.0-1.0
    if output.dtype == np.uint8:
        output = output.astype(np.float32) / 255.0
    return np.clip(output, 0.0, 1.0).astype(np.float32)
```

- [ ] **Step 8: Run tests to verify skeleton works**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py -v`
Expected: All 3 tests PASS (stubs return zeros but the pipeline works end-to-end).

- [ ] **Step 9: Commit**

```bash
git add border_detect/ tests/test_border_detect.py
git commit -m "feat: border_detect package skeleton with 40 stub techniques and ensemble"
```

---

### Task 2: API endpoint and serve.py registration

**Files:**
- Create: `api/endpoints/border_detect.py`
- Modify: `serve.py:221-247`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_border_detect.py`:

```python
def test_api_endpoint_handler():
    """The border_detect endpoint handler should accept params and return border_map."""
    from api.endpoints.border_detect import _handle_border_detect
    import base64
    from PIL import Image
    import io

    # Create a small test image as base64
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_api_endpoint_handler -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.endpoints.border_detect'`

- [ ] **Step 3: Create the endpoint**

Create `api/endpoints/border_detect.py`:

```python
"""Endpoint handler for /api/border-detect — multi-spectrum border detection."""

import base64
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from border_detect import detect_borders
from border_detect.calibrate import load_weights, save_calibration

CALIBRATION_PATH = Path(r"C:\Dev\Image generator\tests\reports\border_calibration.json")


def register(router):
    """Register border detection endpoint."""
    router.register_post("/api/border-detect", _handle_border_detect())


def _handle_border_detect():
    def _handler(params):
        image_b64 = params.get("image")
        if not image_b64:
            return 400, {"error": "Missing required field: image"}

        mode = params.get("mode", "general")

        # Decode base64 image to numpy BGR array
        img_data = base64.b64decode(image_b64)
        img_pil = Image.open(io.BytesIO(img_data)).convert("RGB")
        img_np = np.array(img_pil)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Load calibration weights
        weights = load_weights(CALIBRATION_PATH)

        # Run detection
        result = detect_borders(img_bgr, mode=mode, calibration_weights=weights)

        # Encode border map to base64 PNG
        border_map = result["border_map"]
        _, png_buf = cv2.imencode(".png", border_map)
        border_map_b64 = base64.b64encode(png_buf.tobytes()).decode()

        response = {
            "border_map": border_map_b64,
            "techniques_run": result["techniques_run"],
            "processing_ms": result["processing_ms"],
            "consensus_count": result["consensus_count"],
        }

        # Test mode: add diagnostics and update calibration
        if mode == "test" and "per_technique" in result:
            reference_path = params.get("reference_path")
            v5_border_map_b64 = params.get("v5_border_map")

            diagnostics = _build_diagnostics(
                result["per_technique"], border_map,
                reference_path, v5_border_map_b64, weights
            )
            response["diagnostics"] = diagnostics

            # Update calibration file
            if diagnostics.get("technique_scores"):
                save_calibration(CALIBRATION_PATH, diagnostics["technique_scores"], weights)

        return 200, response

    return _handler


def _build_diagnostics(per_technique, final_map, reference_path, v5_b64, current_weights):
    """Build diagnostic payload for test mode."""
    diagnostics = {"technique_scores": {}, "weight_changes": {}}

    # Load reference if provided
    ref_mask = None
    if reference_path:
        try:
            ref_img = Image.open(reference_path).convert("L")
            ref_mask = np.array(ref_img)
        except Exception:
            pass

    # Load v5+ border map if provided
    v5_mask = None
    if v5_b64:
        try:
            v5_data = base64.b64decode(v5_b64)
            v5_img = Image.open(io.BytesIO(v5_data)).convert("L")
            v5_mask = np.array(v5_img)
        except Exception:
            pass

    # Compute consensus
    h, w = final_map.shape[:2]
    consensus = np.zeros((h, w), dtype=np.int32)
    for output in per_technique.values():
        consensus += (output > 0.5).astype(np.int32)
    consensus_binary = (consensus >= max(1, len(per_technique) // 4)).astype(np.uint8) * 255

    # Score each technique
    for tid, output in per_technique.items():
        binary = (output > 0.5).astype(np.uint8) * 255
        scores = {}

        if ref_mask is not None:
            scores["iou_vs_reference"] = _iou(binary, ref_mask)
        if v5_mask is not None:
            scores["iou_vs_v5plus"] = _iou(binary, v5_mask)
        scores["iou_vs_consensus"] = _iou(binary, consensus_binary)

        # Composite score
        vals = list(scores.values())
        scores["composite"] = sum(vals) / len(vals) if vals else 0.0

        diagnostics["technique_scores"][tid] = scores

    # Rank
    ranked = sorted(diagnostics["technique_scores"].items(),
                    key=lambda x: x[1].get("composite", 0), reverse=True)
    diagnostics["top_5"] = [tid for tid, _ in ranked[:5]]
    diagnostics["bottom_5"] = [tid for tid, _ in ranked[-5:]]

    return diagnostics


def _iou(mask_a, mask_b):
    """Compute IoU between two binary masks (uint8, 0 or 255)."""
    a = mask_a > 127
    b = mask_b > 127
    intersection = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 1.0
    return float(intersection / union)
```

- [ ] **Step 4: Create calibrate.py**

Create `border_detect/calibrate.py`:

```python
"""Calibration engine — load/save/update technique weights."""

import json
from datetime import datetime
from pathlib import Path


def load_weights(path):
    """Load calibration weights from JSON file. Returns dict or None."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("technique_weights")
    except (json.JSONDecodeError, KeyError):
        return None


def save_calibration(path, technique_scores, old_weights):
    """Update calibration file with new scores using EMA smoothing.

    Args:
        path: Path to border_calibration.json
        technique_scores: dict of {tid: {composite: float, ...}}
        old_weights: dict of {tid: float} or None
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data
    existing = {}
    if path.exists():
        try:
            with open(path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass

    # Compute new weights via EMA
    new_weights = {}
    if old_weights is None:
        old_weights = {}
    default_weight = 1.0 / max(len(technique_scores), 1)
    weight_floor = 0.01

    for tid, scores in technique_scores.items():
        composite = scores.get("composite", 0.0)
        old_w = old_weights.get(tid, default_weight)
        # 70/30 EMA: 70% old weight + 30% new score
        new_w = 0.7 * old_w + 0.3 * composite
        new_weights[tid] = max(new_w, weight_floor)

    # Normalize weights to sum to 1.0
    total = sum(new_weights.values())
    if total > 0:
        new_weights = {tid: w / total for tid, w in new_weights.items()}

    # Build calibration data
    history = existing.get("history", [])
    history.append({
        "date": datetime.now().isoformat(),
        "techniques_scored": len(technique_scores),
    })
    # Keep last 50 entries
    history = history[-50:]

    calibration = {
        "version": 1,
        "last_updated": datetime.now().isoformat(),
        "technique_weights": new_weights,
        "technique_scores": {tid: s for tid, s in technique_scores.items()},
        "consensus_threshold": max(1, len(technique_scores) // 4),
        "history": history,
    }

    with open(path, "w") as f:
        json.dump(calibration, f, indent=2)
```

- [ ] **Step 5: Register endpoint in serve.py**

In `serve.py`, find the block at line ~229 where endpoints are registered:

```python
    from api.endpoints import workflow as ep_workflow
```

Add after it:

```python
    from api.endpoints import border_detect as ep_border_detect
```

And find the block at line ~247:

```python
    ep_workflow.register(api_router)
```

Add after it:

```python
    ep_border_detect.register(api_router)
```

- [ ] **Step 6: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 7: Verify serve.py syntax**

Run: `.venv/Scripts/python.exe -c "import py_compile; py_compile.compile('serve.py', doraise=True)"`
Expected: No errors.

- [ ] **Step 8: Commit**

```bash
git add api/endpoints/border_detect.py border_detect/calibrate.py serve.py
git commit -m "feat: /api/border-detect endpoint with calibration engine"
```

---

### Task 3: Implement edge detection techniques (8)

**Files:**
- Modify: `border_detect/techniques/edge.py`

- [ ] **Step 1: Write technique-specific tests**

Add to `tests/test_border_detect.py`:

```python
def test_edge_techniques_produce_output():
    """Each edge technique should return a (H, W) float32 array with some non-zero values."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.edge import TECHNIQUES

    # Create image with a clear vertical edge: left half black, right half white
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    img[:, 25:, :] = 255
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (50, 50), f"{tid} wrong shape: {result.shape}"
        assert result.dtype == np.float32, f"{tid} wrong dtype: {result.dtype}"
        assert result.max() > 0, f"{tid} returned all zeros on image with clear edge"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Run test to verify stubs fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_edge_techniques_produce_output -v`
Expected: FAIL — stubs return all zeros, `assert result.max() > 0` fails.

- [ ] **Step 3: Implement all 8 edge techniques**

Replace `border_detect/techniques/edge.py`:

```python
"""Edge detection techniques (8).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np


def edge_sobel(preprocessed):
    """Sobel operator — first-order gradient magnitude."""
    gray = preprocessed["gray"]
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    mag = mag / mag.max() if mag.max() > 0 else mag
    return mag.astype(np.float32)


def edge_scharr(preprocessed):
    """Scharr operator — optimized rotational symmetry for better diagonals."""
    gray = preprocessed["gray"]
    gx = cv2.Scharr(gray, cv2.CV_64F, 1, 0)
    gy = cv2.Scharr(gray, cv2.CV_64F, 0, 1)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    mag = mag / mag.max() if mag.max() > 0 else mag
    return mag.astype(np.float32)


def edge_prewitt(preprocessed):
    """Prewitt operator — axis-aligned edge specialist."""
    gray = preprocessed["gray"].astype(np.float64)
    kx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float64)
    ky = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float64)
    gx = cv2.filter2D(gray, cv2.CV_64F, kx)
    gy = cv2.filter2D(gray, cv2.CV_64F, ky)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    mag = mag / mag.max() if mag.max() > 0 else mag
    return mag.astype(np.float32)


def edge_roberts(preprocessed):
    """Roberts Cross — fast 2x2 diagonal edge detection."""
    gray = preprocessed["gray"].astype(np.float64)
    k1 = np.array([[1, 0], [0, -1]], dtype=np.float64)
    k2 = np.array([[0, 1], [-1, 0]], dtype=np.float64)
    g1 = cv2.filter2D(gray, cv2.CV_64F, k1)
    g2 = cv2.filter2D(gray, cv2.CV_64F, k2)
    mag = np.sqrt(g1 ** 2 + g2 ** 2)
    mag = mag / mag.max() if mag.max() > 0 else mag
    return mag.astype(np.float32)


def edge_log(preprocessed):
    """Laplacian of Gaussian — orientation-independent, catches curves."""
    gray = preprocessed["gray"]
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
    lap = cv2.Laplacian(blurred, cv2.CV_64F)
    mag = np.abs(lap)
    mag = mag / mag.max() if mag.max() > 0 else mag
    return mag.astype(np.float32)


def edge_dog(preprocessed):
    """Difference of Gaussians — scale-selective, tuned to 15-85px border widths."""
    gray = preprocessed["gray"]
    # sigma1 ~ border inner scale, sigma2 ~ border outer scale
    g1 = cv2.GaussianBlur(gray, (0, 0), sigmaX=2.0).astype(np.float64)
    g2 = cv2.GaussianBlur(gray, (0, 0), sigmaX=8.0).astype(np.float64)
    dog = np.abs(g1 - g2)
    dog = dog / dog.max() if dog.max() > 0 else dog
    return dog.astype(np.float32)


def edge_canny(preprocessed):
    """Canny edge detector — multi-stage with non-maximum suppression."""
    gray = preprocessed["gray"]
    # Adaptive thresholds based on median
    median = np.median(gray)
    low = max(10, int(0.5 * median))
    high = max(30, int(1.5 * median))
    edges = cv2.Canny(gray, low, high)
    return (edges / 255.0).astype(np.float32)


def edge_phase(preprocessed):
    """Phase congruency approximation — illumination-invariant edges.

    Uses multi-scale log-Gabor energy as an approximation of full phase congruency.
    """
    gray = preprocessed["gray"].astype(np.float64)
    h, w = gray.shape
    result = np.zeros((h, w), dtype=np.float64)

    # Multi-scale edge energy using LoG at different scales
    for sigma in [1.0, 2.0, 4.0, 8.0]:
        blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=sigma)
        lap = cv2.Laplacian(blurred, cv2.CV_64F)
        result += np.abs(lap)

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


TECHNIQUES = [
    ("edge_sobel", edge_sobel),
    ("edge_scharr", edge_scharr),
    ("edge_prewitt", edge_prewitt),
    ("edge_roberts", edge_roberts),
    ("edge_log", edge_log),
    ("edge_dog", edge_dog),
    ("edge_canny", edge_canny),
    ("edge_phase", edge_phase),
]
```

- [ ] **Step 4: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_edge_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add border_detect/techniques/edge.py tests/test_border_detect.py
git commit -m "feat: implement 8 edge detection techniques"
```

---

### Task 4: Implement color-space analysis techniques (5)

**Files:**
- Modify: `border_detect/techniques/color.py`

- [ ] **Step 1: Write technique-specific tests**

Add to `tests/test_border_detect.py`:

```python
def test_color_techniques_produce_output():
    """Each color technique should detect transitions on a two-tone image."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.color import TECHNIQUES

    # Image with color transition: left=dark brown (border-like), right=bright
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    img[:, :25, :] = [40, 30, 25]   # dark brown (BGR)
    img[:, 25:, :] = [200, 180, 160]
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (50, 50), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Run test to verify stubs fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_color_techniques_produce_output -v`
Expected: FAIL

- [ ] **Step 3: Implement all 5 color techniques**

Replace `border_detect/techniques/color.py`:

```python
"""Color-space analysis techniques (5).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np


def color_hsv_dark(preprocessed):
    """HSV dark-border mask — low Value, low Saturation targets dark brown/gray borders."""
    hsv = preprocessed["hsv"]
    v = hsv[:, :, 2].astype(np.float32)
    s = hsv[:, :, 1].astype(np.float32)
    # Dark borders: low brightness (V < 80) and low saturation (S < 60)
    dark_score = np.clip(1.0 - v / 80.0, 0, 1)
    achromatic_score = np.clip(1.0 - s / 60.0, 0, 1)
    result = dark_score * achromatic_score
    return result.astype(np.float32)


def color_lab_delta(preprocessed):
    """CIELAB Delta-E transition map — perceptual color distance at each pixel."""
    lab = preprocessed["lab"].astype(np.float64)
    h, w = lab.shape[:2]
    # Compute max Delta-E to 4-connected neighbors
    delta = np.zeros((h, w), dtype=np.float64)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(np.roll(lab, dy, axis=0), dx, axis=1)
        diff = np.sqrt(np.sum((lab - shifted) ** 2, axis=2))
        delta = np.maximum(delta, diff)
    # Zero out border pixels affected by roll wraparound
    delta[0, :] = 0
    delta[-1, :] = 0
    delta[:, 0] = 0
    delta[:, -1] = 0
    delta = delta / delta.max() if delta.max() > 0 else delta
    return delta.astype(np.float32)


def color_ycbcr_luma(preprocessed):
    """YCbCr luminance edges — illumination-robust Sobel on Y channel."""
    ycbcr = preprocessed["ycbcr"]
    y_ch = ycbcr[:, :, 0]
    gx = cv2.Sobel(y_ch, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(y_ch, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    mag = mag / mag.max() if mag.max() > 0 else mag
    return mag.astype(np.float32)


def color_rgb_gradient(preprocessed):
    """RGB Euclidean gradient — max color distance to 4-neighbors (current v5+ method)."""
    rgb = preprocessed["rgb"].astype(np.float64)
    h, w = rgb.shape[:2]
    max_dsq = np.zeros((h, w), dtype=np.float64)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(np.roll(rgb, dy, axis=0), dx, axis=1)
        dsq = np.sum((rgb - shifted) ** 2, axis=2)
        max_dsq = np.maximum(max_dsq, dsq)
    max_dsq[0, :] = 0
    max_dsq[-1, :] = 0
    max_dsq[:, 0] = 0
    max_dsq[:, -1] = 0
    result = np.sqrt(max_dsq)
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def color_achromatic(preprocessed):
    """Dark achromatic filter — near-black low-chroma pixels (current v5+ criteria)."""
    rgb = preprocessed["rgb"].astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    max_ch = np.maximum(np.maximum(r, g), b)
    min_ch = np.minimum(np.minimum(r, g), b)
    spread = max_ch - min_ch
    # Dark (max channel < 55) and achromatic (spread <= 12)
    dark_score = np.clip(1.0 - max_ch / 55.0, 0, 1)
    achromatic_score = np.clip(1.0 - spread / 12.0, 0, 1)
    result = dark_score * achromatic_score
    return result.astype(np.float32)


TECHNIQUES = [
    ("color_hsv_dark", color_hsv_dark),
    ("color_lab_delta", color_lab_delta),
    ("color_ycbcr_luma", color_ycbcr_luma),
    ("color_rgb_gradient", color_rgb_gradient),
    ("color_achromatic", color_achromatic),
]
```

- [ ] **Step 4: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_color_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add border_detect/techniques/color.py tests/test_border_detect.py
git commit -m "feat: implement 5 color-space analysis techniques"
```

---

### Task 5: Implement morphological techniques (5)

**Files:**
- Modify: `border_detect/techniques/morphological.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_morphological_techniques_produce_output():
    """Each morphological technique should detect structures on a bordered image."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.morphological import TECHNIQUES

    # Image with a dark border rectangle
    img = np.full((80, 80, 3), 200, dtype=np.uint8)
    img[10:70, 10:70, :] = 100  # inner panel
    img[8:12, 8:72, :] = 30     # top border
    img[68:72, 8:72, :] = 30    # bottom border
    img[8:72, 8:12, :] = 30     # left border
    img[8:72, 68:72, :] = 30    # right border
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (80, 80), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Implement all 5 techniques**

Replace `border_detect/techniques/morphological.py`:

```python
"""Morphological operation techniques (5).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np


def morph_gradient(preprocessed):
    """Morphological gradient — dilation minus erosion reveals border outlines."""
    gray = preprocessed["gray"]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
    result = grad.astype(np.float32) / 255.0
    return result


def morph_blackhat(preprocessed):
    """Black-hat transform — isolates dark structures sized 15-85px."""
    gray = preprocessed["gray"]
    # Use a kernel sized to the expected border width range
    # Try multiple sizes and take the max response
    result = np.zeros_like(gray, dtype=np.float64)
    for size in [15, 35, 55]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
        bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        result = np.maximum(result, bh.astype(np.float64))
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def morph_close_gaps(preprocessed):
    """Multi-scale closing — bridges small gaps in detected border fragments."""
    gray = preprocessed["gray"]
    # Invert so borders (dark) become bright for closing
    inv = 255 - gray
    result = np.zeros_like(inv, dtype=np.float64)
    for size in [3, 7, 15]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
        closed = cv2.morphologyEx(inv, cv2.MORPH_CLOSE, kernel)
        result = np.maximum(result, closed.astype(np.float64))
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def morph_tophat(preprocessed):
    """White top-hat — extracts bright details/highlights from dark border regions."""
    gray = preprocessed["gray"]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    th = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    result = th.astype(np.float32) / 255.0
    return result


def morph_width_probe(preprocessed):
    """Erosion-dilation width probe — detects borders matching expected widths."""
    gray = preprocessed["gray"]
    inv = 255 - gray  # borders bright
    h, w = gray.shape
    result = np.zeros((h, w), dtype=np.float64)

    # Erode at increasing sizes — structures that survive N erosions are >= 2N+1 px wide
    for radius in [3, 7, 12, 20]:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
        eroded = cv2.erode(inv, kernel)
        dilated = cv2.dilate(eroded, kernel)
        # Structures that survived are at least this wide
        result = np.maximum(result, dilated.astype(np.float64))

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


TECHNIQUES = [
    ("morph_gradient", morph_gradient),
    ("morph_blackhat", morph_blackhat),
    ("morph_close_gaps", morph_close_gaps),
    ("morph_tophat", morph_tophat),
    ("morph_width_probe", morph_width_probe),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_morphological_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/morphological.py tests/test_border_detect.py
git commit -m "feat: implement 5 morphological border detection techniques"
```

---

### Task 6: Implement texture analysis techniques (4)

**Files:**
- Modify: `border_detect/techniques/texture.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_texture_techniques_produce_output():
    """Each texture technique should differentiate textured vs smooth regions."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.texture import TECHNIQUES

    # Left half: noisy texture (scene-like). Right half: smooth (panel-like)
    img = np.random.randint(50, 200, (60, 60, 3), dtype=np.uint8)
    img[:, 30:, :] = 128  # uniform right half
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Implement all 4 techniques**

Replace `border_detect/techniques/texture.py`:

```python
"""Texture analysis techniques (4).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops


def tex_lbp(preprocessed):
    """Local Binary Patterns — texture classification (border vs panel vs scene)."""
    gray = preprocessed["gray"]
    lbp = local_binary_pattern(gray, P=8, R=1, method="uniform")
    # LBP values indicate texture type — edges have high LBP variance locally
    # Compute local variance of LBP as border indicator
    lbp_f = lbp.astype(np.float32)
    mean = cv2.blur(lbp_f, (11, 11))
    sq_mean = cv2.blur(lbp_f ** 2, (11, 11))
    variance = sq_mean - mean ** 2
    variance = np.maximum(variance, 0)
    result = variance / variance.max() if variance.max() > 0 else variance
    return result.astype(np.float32)


def tex_gabor(preprocessed):
    """Gabor filter bank — orientation-selective texture at multiple scales."""
    gray = preprocessed["gray"].astype(np.float64)
    h, w = gray.shape
    result = np.zeros((h, w), dtype=np.float64)

    for theta in [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
        for sigma in [2.0, 4.0, 8.0]:
            kernel = cv2.getGaborKernel(
                (21, 21), sigma=sigma, theta=theta,
                lambd=sigma * 2, gamma=0.5, psi=0
            )
            filtered = cv2.filter2D(gray, cv2.CV_64F, kernel)
            result = np.maximum(result, np.abs(filtered))

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def tex_glcm(preprocessed):
    """GLCM contrast — sliding window texture statistics via gray-level co-occurrence."""
    gray = preprocessed["gray"]
    h, w = gray.shape
    # Downsample to 8 gray levels for speed
    quantized = (gray // 32).astype(np.uint8)
    result = np.zeros((h, w), dtype=np.float32)

    # Compute GLCM contrast in sliding windows
    win = 16
    step = 4  # stride for speed
    for y in range(0, h - win, step):
        for x in range(0, w - win, step):
            patch = quantized[y:y + win, x:x + win]
            glcm = graycomatrix(patch, distances=[1], angles=[0], levels=8,
                                symmetric=True, normed=True)
            contrast = graycoprops(glcm, "contrast")[0, 0]
            result[y:y + step, x:x + step] = contrast

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def tex_laws(preprocessed):
    """Laws texture energy — edge/spot fingerprints using 5-element kernels."""
    gray = preprocessed["gray"].astype(np.float64)

    # Laws 1D kernels
    L5 = np.array([1, 4, 6, 4, 1], dtype=np.float64)     # Level
    E5 = np.array([-1, -2, 0, 2, 1], dtype=np.float64)    # Edge
    S5 = np.array([-1, 0, 2, 0, -1], dtype=np.float64)    # Spot

    # Build 2D kernels from outer products
    result = np.zeros_like(gray, dtype=np.float64)
    for k1 in [L5, E5, S5]:
        for k2 in [L5, E5, S5]:
            kernel = np.outer(k1, k2)
            filtered = cv2.filter2D(gray, cv2.CV_64F, kernel)
            energy = cv2.blur(np.abs(filtered), (15, 15))
            result = np.maximum(result, energy)

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


TECHNIQUES = [
    ("tex_lbp", tex_lbp),
    ("tex_gabor", tex_gabor),
    ("tex_glcm", tex_glcm),
    ("tex_laws", tex_laws),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_texture_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/texture.py tests/test_border_detect.py
git commit -m "feat: implement 4 texture analysis techniques"
```

---

### Task 7: Implement statistical method techniques (4)

**Files:**
- Modify: `border_detect/techniques/statistical.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_statistical_techniques_produce_output():
    """Each statistical technique should differentiate uniform vs varied regions."""
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
```

- [ ] **Step 2: Implement all 4 techniques**

Replace `border_detect/techniques/statistical.py`:

```python
"""Statistical method techniques (4).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np
from skimage.filters.rank import entropy
from skimage.morphology import disk


def stat_variance(preprocessed):
    """Local variance map — smooth panels (low) vs textured scenes (high)."""
    gray = preprocessed["gray"].astype(np.float64)
    win = 11
    mean = cv2.blur(gray, (win, win))
    sq_mean = cv2.blur(gray ** 2, (win, win))
    variance = sq_mean - mean ** 2
    variance = np.maximum(variance, 0)
    result = variance / variance.max() if variance.max() > 0 else variance
    return result.astype(np.float32)


def stat_entropy(preprocessed):
    """Local entropy map — region complexity measure."""
    gray = preprocessed["gray"]
    ent = entropy(gray, disk(5))
    result = ent.astype(np.float64)
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def stat_mahalanobis(preprocessed):
    """Mahalanobis color distance — classify pixels into border/panel/background clusters."""
    rgb = preprocessed["rgb"].astype(np.float64)
    h, w = rgb.shape[:2]
    pixels = rgb.reshape(-1, 3)

    # K-means with 3 clusters (border, panel, background)
    pixels_f32 = pixels.astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels_f32, 3, None, criteria, 3, cv2.KMEANS_PP_CENTERS)

    # Compute distance from each pixel to its cluster center
    labels = labels.flatten()
    distances = np.zeros(len(pixels), dtype=np.float64)
    for i in range(3):
        mask = labels == i
        if mask.sum() == 0:
            continue
        cluster_pixels = pixels[mask]
        center = centers[i]
        distances[mask] = np.sqrt(np.sum((cluster_pixels - center) ** 2, axis=1))

    result = distances.reshape(h, w)
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def stat_mean_diff(preprocessed):
    """Adaptive mean color difference — pixels differing from local average."""
    rgb = preprocessed["rgb"].astype(np.float64)
    win = 15
    result = np.zeros(rgb.shape[:2], dtype=np.float64)
    for ch in range(3):
        channel = rgb[:, :, ch]
        local_mean = cv2.blur(channel, (win, win))
        diff = np.abs(channel - local_mean)
        result = np.maximum(result, diff)
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


TECHNIQUES = [
    ("stat_variance", stat_variance),
    ("stat_entropy", stat_entropy),
    ("stat_mahalanobis", stat_mahalanobis),
    ("stat_mean_diff", stat_mean_diff),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_statistical_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/statistical.py tests/test_border_detect.py
git commit -m "feat: implement 4 statistical method techniques"
```

---

### Task 8: Implement gradient analysis techniques (3)

**Files:**
- Modify: `border_detect/techniques/gradient.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_gradient_techniques_produce_output():
    """Each gradient technique should detect structure on an image with corners."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.gradient import TECHNIQUES

    # Image with a bright rectangle (has corners and edges)
    img = np.full((60, 60, 3), 50, dtype=np.uint8)
    img[15:45, 15:45, :] = 200
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Implement all 3 techniques**

Replace `border_detect/techniques/gradient.py`:

```python
"""Gradient analysis techniques (3).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np
from skimage.feature import structure_tensor, structure_tensor_eigenvalues


def grad_structure(preprocessed):
    """Structure tensor — classify each pixel as edge, corner, or flat."""
    gray = preprocessed["gray"].astype(np.float64)
    Axx, Axy, Ayy = structure_tensor(gray, sigma=1.5)
    l1, l2 = structure_tensor_eigenvalues(Axx, Axy, Ayy)
    # Edge strength: large l1, small l2 → strong edge
    # Use l1 as edge indicator (largest eigenvalue)
    result = l1 / l1.max() if l1.max() > 0 else l1
    return result.astype(np.float32)


def grad_harris(preprocessed):
    """Harris corner detection — finds border frame corner points."""
    gray = preprocessed["gray"].astype(np.float32)
    harris = cv2.cornerHarris(gray, blockSize=3, ksize=3, k=0.04)
    # Dilate to make corners more visible as areas
    harris = cv2.dilate(harris, None)
    result = np.maximum(harris, 0)
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def grad_hog(preprocessed):
    """Oriented gradient histogram per cell — region type by gradient distribution."""
    gray = preprocessed["gray"]
    h, w = gray.shape

    # Compute gradient magnitude and direction
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    angle = np.arctan2(gy, gx) % np.pi  # 0 to pi

    # Cell-based gradient energy: high energy = edge region
    cell_size = 8
    result = np.zeros((h, w), dtype=np.float64)
    for cy in range(0, h - cell_size, cell_size):
        for cx in range(0, w - cell_size, cell_size):
            cell_mag = mag[cy:cy + cell_size, cx:cx + cell_size]
            energy = cell_mag.mean()
            result[cy:cy + cell_size, cx:cx + cell_size] = energy

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


TECHNIQUES = [
    ("grad_structure", grad_structure),
    ("grad_harris", grad_harris),
    ("grad_hog", grad_hog),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_gradient_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/gradient.py tests/test_border_detect.py
git commit -m "feat: implement 3 gradient analysis techniques"
```

---

### Task 9: Implement structural analysis techniques (4)

**Files:**
- Modify: `border_detect/techniques/structural.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_structural_techniques_produce_output():
    """Each structural technique should detect regions on a bordered image."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.structural import TECHNIQUES

    # White image with dark nested rectangles (contour hierarchy)
    img = np.full((80, 80, 3), 220, dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (70, 70), (30, 30, 30), 3)
    cv2.rectangle(img, (20, 20), (60, 60), (30, 30, 30), 3)
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (80, 80), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Implement all 4 techniques**

Replace `border_detect/techniques/structural.py`:

```python
"""Structural analysis techniques (4).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np


def struct_contour(preprocessed):
    """Contour hierarchy — nested contour tree. Deeper nesting = more UI-like."""
    gray = preprocessed["gray"]
    h, w = gray.shape

    # Adaptive threshold to binarize
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 11, 2)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if hierarchy is None or len(contours) == 0:
        return np.zeros((h, w), dtype=np.float32)

    hierarchy = hierarchy[0]  # shape: (N, 4) — [next, prev, child, parent]
    result = np.zeros((h, w), dtype=np.float32)

    # Compute depth for each contour
    depths = np.zeros(len(contours), dtype=np.int32)
    for i in range(len(contours)):
        depth = 0
        parent = hierarchy[i][3]
        while parent >= 0:
            depth += 1
            parent = hierarchy[parent][3]
        depths[i] = depth

    max_depth = depths.max() if len(depths) > 0 else 1

    # Draw contours weighted by depth (deeper = more border-like)
    for i, contour in enumerate(contours):
        weight = depths[i] / max_depth if max_depth > 0 else 0
        cv2.drawContours(result, [contour], -1, float(weight), 2)

    return result.astype(np.float32)


def struct_ccl(preprocessed):
    """Connected component labeling — detect region boundaries by label transitions."""
    gray = preprocessed["gray"]
    h, w = gray.shape

    # Otsu threshold
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)

    # Boundary map: pixels where label differs from neighbor
    result = np.zeros((h, w), dtype=np.float32)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(np.roll(labels, dy, axis=0), dx, axis=1)
        result += (labels != shifted).astype(np.float32)

    result = np.clip(result, 0, 1)
    result[0, :] = 0
    result[-1, :] = 0
    result[:, 0] = 0
    result[:, -1] = 0
    return result.astype(np.float32)


def struct_distance(preprocessed):
    """Distance transform — border centerline and width measurement."""
    gray = preprocessed["gray"]
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    # Borders have moderate distance values (not too thick, not too thin)
    # Use Laplacian of distance to find ridges (border centers)
    lap = cv2.Laplacian(dist, cv2.CV_64F)
    ridge = np.abs(lap)
    ridge = ridge / ridge.max() if ridge.max() > 0 else ridge
    return ridge.astype(np.float32)


def struct_watershed(preprocessed):
    """Watershed segmentation — gradient-based region boundary extraction."""
    gray = preprocessed["gray"]
    bgr = preprocessed["bgr"]
    h, w = gray.shape

    # Gradient as input surface
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

    # Markers from sure foreground/background via threshold
    _, sure_fg = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    sure_fg = cv2.erode(sure_fg, None, iterations=2)
    sure_bg = cv2.dilate(sure_fg, None, iterations=3)
    unknown = cv2.subtract(sure_bg, sure_fg)

    _, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown == 255] = 0

    markers_ws = cv2.watershed(bgr.copy(), markers.copy())

    # Watershed boundaries are marked as -1
    result = np.zeros((h, w), dtype=np.float32)
    result[markers_ws == -1] = 1.0
    # Dilate boundaries slightly for visibility
    result = cv2.dilate(result, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    return result.astype(np.float32)


TECHNIQUES = [
    ("struct_contour", struct_contour),
    ("struct_ccl", struct_ccl),
    ("struct_distance", struct_distance),
    ("struct_watershed", struct_watershed),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_structural_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/structural.py tests/test_border_detect.py
git commit -m "feat: implement 4 structural analysis techniques"
```

---

### Task 10: Implement adaptive & frequency techniques (4)

**Files:**
- Modify: `border_detect/techniques/adaptive.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_adaptive_techniques_produce_output():
    """Each adaptive/frequency technique should detect features."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.adaptive import TECHNIQUES

    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:, 32:, :] = 255
    # Add some noise for frequency techniques
    noise = np.random.randint(0, 30, img.shape, dtype=np.uint8)
    img = cv2.add(img, noise)
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (64, 64), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Implement all 4 techniques**

Replace `border_detect/techniques/adaptive.py`:

```python
"""Adaptive thresholding & frequency domain techniques (4).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np
from skimage.filters import threshold_sauvola, threshold_niblack


def adapt_sauvola(preprocessed):
    """Sauvola adaptive threshold — handles varying background brightness."""
    gray = preprocessed["gray"]
    thresh = threshold_sauvola(gray, window_size=25, k=0.2)
    binary = (gray < thresh).astype(np.float32)
    return binary


def adapt_niblack(preprocessed):
    """Niblack adaptive threshold — alternative adaptive binarization."""
    gray = preprocessed["gray"]
    thresh = threshold_niblack(gray, window_size=25, k=0.8)
    binary = (gray < thresh).astype(np.float32)
    return binary


def freq_fft_highpass(preprocessed):
    """FFT high-pass filter — keeps edge frequencies, removes background."""
    gray = preprocessed["gray"].astype(np.float64)
    h, w = gray.shape

    # FFT
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)

    # High-pass mask: block low frequencies (center)
    cy, cx = h // 2, w // 2
    radius = min(h, w) // 10  # block ~10% of spectrum
    mask = np.ones((h, w), dtype=np.float64)
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
    mask[dist <= radius] = 0
    # Smooth transition
    transition = np.clip((dist - radius) / (radius * 0.5), 0, 1)
    mask = np.maximum(mask, transition)

    # Apply and inverse FFT
    filtered = fshift * mask
    f_ishift = np.fft.ifftshift(filtered)
    result = np.abs(np.fft.ifft2(f_ishift))
    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


def freq_wavelet(preprocessed):
    """Wavelet multi-scale edges — detect borders at multiple resolutions."""
    gray = preprocessed["gray"].astype(np.float64)
    h, w = gray.shape

    try:
        import pywt
        # 2-level DWT decomposition
        result = np.zeros((h, w), dtype=np.float64)
        for level in range(1, 4):
            coeffs = pywt.dwt2(gray, "haar")
            cA, (cH, cV, cD) = coeffs
            # Combine detail coefficients (edges at this scale)
            detail = np.sqrt(cH ** 2 + cV ** 2 + cD ** 2)
            # Upscale back to original size
            detail_up = cv2.resize(detail, (w, h), interpolation=cv2.INTER_LINEAR)
            result = np.maximum(result, detail_up)
            gray = cA  # next level works on approximation
    except ImportError:
        # Fallback: multi-scale LoG
        for sigma in [1.0, 2.0, 4.0]:
            blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=sigma)
            lap = np.abs(cv2.Laplacian(blurred, cv2.CV_64F))
            result = np.maximum(result, lap) if 'result' in dir() else lap

    result = result / result.max() if result.max() > 0 else result
    return result.astype(np.float32)


TECHNIQUES = [
    ("adapt_sauvola", adapt_sauvola),
    ("adapt_niblack", adapt_niblack),
    ("freq_fft_highpass", freq_fft_highpass),
    ("freq_wavelet", freq_wavelet),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_adaptive_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/adaptive.py tests/test_border_detect.py
git commit -m "feat: implement 4 adaptive and frequency domain techniques"
```

---

### Task 11: Implement color quantization & grouping techniques (3)

**Files:**
- Modify: `border_detect/techniques/quantization.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_border_detect.py`:

```python
def test_quantization_techniques_produce_output():
    """Each quantization technique should find region boundaries."""
    from border_detect.preprocess import preprocess
    from border_detect.techniques.quantization import TECHNIQUES

    # 3-color image: dark border, medium panel, bright background
    img = np.full((60, 60, 3), 200, dtype=np.uint8)
    img[10:50, 10:50, :] = 100
    img[8:12, 8:52, :] = 30
    img[48:52, 8:52, :] = 30
    img[8:52, 8:12, :] = 30
    img[8:52, 48:52, :] = 30
    preprocessed = preprocess(img)

    for tid, fn in TECHNIQUES:
        result = fn(preprocessed)
        assert result.shape == (60, 60), f"{tid} wrong shape"
        assert result.dtype == np.float32, f"{tid} wrong dtype"
        assert result.max() > 0, f"{tid} returned all zeros"
        assert 0.0 <= result.min() and result.max() <= 1.0, f"{tid} out of range"
```

- [ ] **Step 2: Implement all 3 techniques**

Replace `border_detect/techniques/quantization.py`:

```python
"""Color quantization & grouping techniques (3).

Each function takes a preprocessed dict and returns a (H, W) float32 array in [0, 1].
"""

import cv2
import numpy as np
from skimage.segmentation import slic


def quant_median(preprocessed):
    """Median cut quantization — reduce to 8 colors, detect boundaries between them."""
    rgb = preprocessed["rgb"]
    h, w = rgb.shape[:2]

    # Quantize to 8 colors using K-means (simulating median cut)
    pixels = rgb.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, _ = cv2.kmeans(pixels, 8, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(h, w)

    # Boundary map: pixels where quantized label differs from neighbor
    result = np.zeros((h, w), dtype=np.float32)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(np.roll(labels, dy, axis=0), dx, axis=1)
        result += (labels != shifted).astype(np.float32)
    result = np.clip(result, 0, 1)
    result[0, :] = 0
    result[-1, :] = 0
    result[:, 0] = 0
    result[:, -1] = 0
    return result.astype(np.float32)


def quant_kmeans(preprocessed):
    """K-means color clustering — guided by 3 clusters (border, panel, background)."""
    rgb = preprocessed["rgb"]
    h, w = rgb.shape[:2]
    pixels = rgb.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(h, w)

    # Find the darkest cluster (likely border)
    brightness = centers.sum(axis=1)
    border_label = brightness.argmin()

    # Border confidence = membership in darkest cluster
    result = (labels == border_label).astype(np.float32)
    return result


def quant_slic(preprocessed):
    """SLIC superpixel boundaries — region borders between similar pixel groups."""
    rgb = preprocessed["rgb"]
    h, w = rgb.shape[:2]

    # SLIC superpixels
    segments = slic(rgb, n_segments=200, compactness=10, start_label=0)

    # Boundary map
    result = np.zeros((h, w), dtype=np.float32)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(np.roll(segments, dy, axis=0), dx, axis=1)
        result += (segments != shifted).astype(np.float32)
    result = np.clip(result, 0, 1)
    result[0, :] = 0
    result[-1, :] = 0
    result[:, 0] = 0
    result[:, -1] = 0
    return result.astype(np.float32)


TECHNIQUES = [
    ("quant_median", quant_median),
    ("quant_kmeans", quant_kmeans),
    ("quant_slic", quant_slic),
]
```

- [ ] **Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py::test_quantization_techniques_produce_output -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add border_detect/techniques/quantization.py tests/test_border_detect.py
git commit -m "feat: implement 3 color quantization and grouping techniques"
```

---

### Task 12: app.js integration — call /api/border-detect

**Files:**
- Modify: `app.js:2380-2400`

- [ ] **Step 1: Add async border detection call before v5+ fallback**

In `app.js`, find line 2390:

```javascript
    let hybridAlpha = buildBlackBorderUiMask(sourceData, loadedImage.width, loadedImage.height);
```

Replace the section from line 2387 to line 2390 with:

```javascript
    // Step 1: Try multi-spectrum border detection via server
    console.log(`[AI Remove v6] Starting detection on ${loadedImage.width}x${loadedImage.height} image`);
    let multiSpectrumMap = null;
    try {
      const canvasTmp = document.createElement('canvas');
      canvasTmp.width = loadedImage.width;
      canvasTmp.height = loadedImage.height;
      const ctxTmp = canvasTmp.getContext('2d');
      ctxTmp.drawImage(loadedImage, 0, 0);
      const b64 = canvasTmp.toDataURL('image/png').split(',')[1];
      const resp = await fetch('/api/border-detect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image: b64, width: loadedImage.width, height: loadedImage.height, mode: 'general'})
      });
      if (resp.ok) {
        const result = await resp.json();
        console.log(`[AI Remove v6] Multi-spectrum: ${result.techniques_run} techniques, ${result.processing_ms}ms, consensus=${result.consensus_count}`);
        // Decode border map from base64 PNG to ImageData
        const mapImg = new Image();
        await new Promise((resolve, reject) => {
          mapImg.onload = resolve;
          mapImg.onerror = reject;
          mapImg.src = 'data:image/png;base64,' + result.border_map;
        });
        const mapCanvas = document.createElement('canvas');
        mapCanvas.width = loadedImage.width;
        mapCanvas.height = loadedImage.height;
        const mapCtx = mapCanvas.getContext('2d');
        mapCtx.drawImage(mapImg, 0, 0);
        const mapData = mapCtx.getImageData(0, 0, loadedImage.width, loadedImage.height);
        // Convert grayscale border map to alpha mask (Uint8Array)
        multiSpectrumMap = new Uint8Array(loadedImage.width * loadedImage.height);
        for (let i = 0; i < multiSpectrumMap.length; i++) {
          multiSpectrumMap[i] = mapData.data[i * 4]; // R channel of grayscale = border confidence
        }
      }
    } catch (e) {
      console.log('[AI Remove v6] Multi-spectrum unavailable, using v5+ fallback:', e.message || e);
    }

    // Step 2: Generate mask — use multi-spectrum result or fall back to v5+
    let hybridAlpha;
    if (multiSpectrumMap) {
      hybridAlpha = multiSpectrumMap;
      console.log('[AI Remove v6] Using multi-spectrum border map');
    } else {
      hybridAlpha = buildBlackBorderUiMask(sourceData, loadedImage.width, loadedImage.height);
    }
```

- [ ] **Step 2: Verify JS syntax**

Run: `node --check app.js`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "feat: integrate multi-spectrum border detection into AI Remove workflow"
```

---

### Task 13: Create diagnostic skill

**Files:**
- Create: `.claude/skills/border-detect/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `.claude/skills/border-detect/SKILL.md`:

```markdown
---
name: border-detect
description: Run multi-spectrum border detection diagnostic on an image — shows all 40 techniques ranked, agreement analysis, calibration weights.
---

# Border Detection Diagnostic

Run the full 40-technique multi-spectrum border detector in test mode and display a diagnostic report.

## Steps

1. **Ensure server is running:**
   - Check if serve.py is responding at http://127.0.0.1:8080
   - If not, start it via `tests/helpers/server_manager.py`

2. **Select test image:**
   - If user specified an image path, use that
   - Otherwise use the dark reference source: `input/Example quality image extraction/Dark background examples/Original Image dark background.png`

3. **Call /api/border-detect in test mode:**
   ```bash
   .venv/Scripts/python.exe -c "
   import base64, json, urllib.request
   from pathlib import Path

   img_path = '<IMAGE_PATH>'
   ref_path = 'input/Example quality image extraction/Dark background examples/example preview ectraction dark background removed.PNG'

   with open(img_path, 'rb') as f:
       img_b64 = base64.b64encode(f.read()).decode()

   payload = json.dumps({
       'image': img_b64,
       'mode': 'test',
       'reference_path': ref_path
   }).encode()

   req = urllib.request.Request(
       'http://127.0.0.1:8080/api/border-detect',
       data=payload,
       headers={'Content-Type': 'application/json'}
   )
   with urllib.request.urlopen(req, timeout=30) as resp:
       result = json.loads(resp.read())

   print(f'Techniques run: {result[\"techniques_run\"]}')
   print(f'Processing time: {result[\"processing_ms\"]}ms')
   print(f'Max consensus: {result[\"consensus_count\"]} techniques agree')

   if 'diagnostics' in result:
       d = result['diagnostics']
       print(f'\\nTOP 5 techniques: {d[\"top_5\"]}')
       print(f'BOTTOM 5 techniques: {d[\"bottom_5\"]}')
       print('\\nAll technique scores:')
       for tid, scores in sorted(d['technique_scores'].items(), key=lambda x: x[1].get('composite', 0), reverse=True):
           print(f'  {tid:25s} composite={scores.get(\"composite\", 0):.4f}  ref={scores.get(\"iou_vs_reference\", \"N/A\")}  consensus={scores.get(\"iou_vs_consensus\", 0):.4f}')
   "
   ```

4. **Report results:**
   - Print the ranked technique scorecard
   - Highlight which techniques agree/disagree
   - Show calibration weight changes if any
   - Note the overall border map quality (IoU vs reference if available)

5. **Save artifacts:**
   - Border map saved to `tests/reports/border_detect/`
   - Calibration updated in `tests/reports/border_calibration.json`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/border-detect/SKILL.md
git commit -m "feat: add /border-detect diagnostic skill"
```

---

### Task 14: Full integration test

**Files:**
- No new files

- [ ] **Step 1: Run all border_detect unit tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_border_detect.py -v`
Expected: All tests PASS (skeleton + all 9 technique categories + API endpoint).

- [ ] **Step 2: Start server and test endpoint manually**

Run:
```bash
.venv/Scripts/python.exe -c "
import base64, json, urllib.request, time
from pathlib import Path

img_path = r'C:\Dev\Image generator\input\Example quality image extraction\Dark background examples\Original Image dark background.png'
with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = json.dumps({'image': img_b64, 'mode': 'general'}).encode()
req = urllib.request.Request('http://127.0.0.1:8080/api/border-detect', data=payload, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(f'Status: OK')
    print(f'Techniques: {result[\"techniques_run\"]}')
    print(f'Time: {result[\"processing_ms\"]}ms')
    print(f'Consensus: {result[\"consensus_count\"]}')
    print(f'Border map size: {len(result[\"border_map\"])} chars base64')
"
```
Expected: 40 techniques, <3000ms, valid border map returned.

- [ ] **Step 3: Run full test suite via launcher**

Run: `.venv/Scripts/python.exe tests/launcher.py -v`
Expected: All existing tests still pass. No regressions. Border detect tests also pass.

- [ ] **Step 4: Test the production dark image end-to-end**

Run: `.venv/Scripts/python.exe tests/launcher.py tests/test_production.py -v`
Expected: Production tests execute using the multi-spectrum detector (look for "Multi-spectrum:" in console output). May pass or fail on quality metrics — the point is the pipeline works end-to-end.

- [ ] **Step 5: Commit test file cleanup if needed**

```bash
git add tests/test_border_detect.py
git commit -m "test: finalize border detection integration tests"
```
