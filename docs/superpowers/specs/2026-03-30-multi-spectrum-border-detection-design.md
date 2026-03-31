# Multi-Spectrum Border Detection — Design Spec

## Goal

Replace the current dual-criteria border detection (gradient + dark achromatic) with a 40-technique multi-spectrum ensemble that runs on **every image the app processes**. The detector runs Python-side via serve.py using opencv-python, scikit-image, and numpy. A self-calibrating weighted ensemble combines all technique outputs into a single border confidence map. Calibration weights are learned from test runs against reference images and updated automatically.

A `/border-detect` skill provides diagnostic output for manual inspection.

## Core Requirements

1. **Every image processed by the app goes through the multi-spectrum detector.** This is the production path, not an optional enhancement. When `buildBlackBorderUiMask()` runs, it calls `/api/border-detect` to get the border map.
2. **Fallback to current detection when server unavailable.** If serve.py isn't running (direct `index.html` open), app.js falls back to the existing gradient+achromatic dual criteria.
3. **Self-calibrating ensemble.** Technique weights are stored in `tests/reports/border_calibration.json`. Production test runs re-calibrate weights. New installs start with equal weights (pure consensus).
4. **Diagnostic skill.** `/border-detect` runs the full analysis with per-technique breakdown, agreement maps, and calibration details.
5. **Performance target.** <3 seconds per image (1920x1080) for all 40 techniques combined.

## Architecture

### Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `border_detect/__init__.py` | Project root | Package init, exposes `detect_borders()` |
| `border_detect/ensemble.py` | Project root | Load calibration weights, combine technique outputs, produce final border map |
| `border_detect/calibrate.py` | Project root | Score techniques against references, update calibration JSON |
| `border_detect/techniques/edge.py` | Project root | 8 edge detection techniques |
| `border_detect/techniques/color.py` | Project root | 5 color-space analysis techniques |
| `border_detect/techniques/morphological.py` | Project root | 5 morphological operations |
| `border_detect/techniques/texture.py` | Project root | 4 texture analysis techniques |
| `border_detect/techniques/statistical.py` | Project root | 4 statistical methods |
| `border_detect/techniques/gradient.py` | Project root | 3 gradient analysis techniques |
| `border_detect/techniques/structural.py` | Project root | 4 structural analysis techniques |
| `border_detect/techniques/adaptive.py` | Project root | 4 adaptive & frequency techniques |
| `border_detect/techniques/quantization.py` | Project root | 3 color quantization & grouping techniques |
| `api/endpoints/border_detect.py` | Project root | serve.py endpoint `/api/border-detect` |
| `.claude/skills/border-detect/SKILL.md` | Project root | Diagnostic skill definition |
| `tests/reports/border_calibration.json` | Project root | Persisted per-technique weights |

### Dependencies (pip install)

- `opencv-python` — morphological ops, contour hierarchy, bilateral filter, Canny, watershed, SLIC, Gabor, adaptive thresholding
- `scikit-image` — LBP, GLCM, phase congruency, structure tensor, Sauvola/Niblack, wavelet edges
- `numpy` — already installed, array operations for all techniques
- `scipy` — already installed (via scikit-image), FFT, distance transform
- `PyWavelets` — wavelet transforms for multi-scale edge detection (`pywt.dwt2`)
- `scikit-learn` — optional future upgrade for learned classifier weights (not required for v1 weighted voting)

## Operating Modes

### General Mode (A+C) — Every Image

Runs on every image the app processes via `/api/border-detect`.

- Runs all 40 techniques
- Combines via calibrated weighted ensemble
- Also computes consensus map (pixels detected by N+ techniques = high confidence)
- Returns single border confidence map (grayscale PNG, 0-255)
- Uses stored calibration weights from `border_calibration.json`
- If no calibration file exists, uses equal weights (pure consensus)

### Test Mode (D) — Production Tests

Activated when the endpoint receives `mode: "test"` with reference image paths.

- Everything in General Mode, plus:
- Compares each technique's output against v5+ current border detection
- Compares each technique's output against reference extraction images
- Compares each technique against consensus
- Computes per-technique scores: IoU, precision, recall, F1
- Updates `border_calibration.json` with new weights
- Returns full diagnostic payload alongside the border map

### Diagnostic Skill Mode — Manual

Invoked via `/border-detect` skill in Claude Code.

- Runs Test Mode (D) on a specified image
- Prints ranked scorecard of all 40 techniques
- Shows technique agreement/disagreement regions
- Reports calibration weight changes
- Saves full comparison artifacts to temp directory

## Technique Inventory (40 Techniques)

### 1. Edge Detection (8)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `edge_sobel` | Sobel operator | First-order gradient edges | `cv2.Sobel` Gx+Gy magnitude |
| `edge_scharr` | Scharr operator | Edges with better rotational symmetry | `cv2.Scharr` Gx+Gy magnitude |
| `edge_prewitt` | Prewitt operator | Axis-aligned edges | numpy 3x3 convolution |
| `edge_roberts` | Roberts Cross | Fast diagonal edges | numpy 2x2 convolution |
| `edge_log` | Laplacian of Gaussian | Orientation-independent edges, curves | `cv2.GaussianBlur` + `cv2.Laplacian` |
| `edge_dog` | Difference of Gaussians | Scale-selective edges (tuned to 15-85px) | Two `cv2.GaussianBlur` subtracted |
| `edge_canny` | Canny edge detector | Multi-stage thin edges | `cv2.Canny` |
| `edge_phase` | Phase congruency | Illumination-invariant edges | `skimage.filters` or manual Kovesi |

### 2. Color-Space Analysis (5)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `color_hsv_dark` | HSV dark-border mask | Low-V low-S pixels (dark brown/gray borders) | `cv2.cvtColor` HSV, threshold V and S |
| `color_lab_delta` | CIELAB Delta-E map | Perceptual color transitions | `cv2.cvtColor` LAB, local Delta-E |
| `color_ycbcr_luma` | YCbCr luminance edges | Illumination-robust edges | Convert to YCbCr, Sobel on Y channel |
| `color_rgb_gradient` | RGB Euclidean gradient | Color transitions (current v5+ method) | Per-pixel Euclidean distance to neighbors |
| `color_achromatic` | Dark achromatic filter | Near-black low-chroma pixels (current v5+) | maxCh<55, spread<=12, distToEdge<=2 |

### 3. Morphological Operations (5)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `morph_gradient` | Morphological gradient | Border outlines via dilation-erosion | `cv2.morphologyEx` MORPH_GRADIENT |
| `morph_blackhat` | Black-hat transform | Dark borders sized 15-85px | `cv2.morphologyEx` MORPH_BLACKHAT |
| `morph_close_gaps` | Multi-scale closing | Bridged gaps in border detections | `cv2.morphologyEx` MORPH_CLOSE at 3 scales |
| `morph_tophat` | White top-hat | Highlights/details in dark regions | `cv2.morphologyEx` MORPH_TOPHAT |
| `morph_width_probe` | Erosion-dilation probe | Borders matching expected widths | Erode at multiple sizes, compare |

### 4. Texture Analysis (4)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `tex_lbp` | Local Binary Patterns | Texture class (border vs panel vs scene) | `skimage.feature.local_binary_pattern` |
| `tex_gabor` | Gabor filter bank | Oriented textures at multiple scales | `cv2.getGaborKernel` 4 orientations x 3 scales |
| `tex_glcm` | GLCM contrast/energy | Sliding window texture statistics | `skimage.feature.graycomatrix` |
| `tex_laws` | Laws texture energy | Edge/spot texture fingerprints | numpy 5x5 kernel convolutions (L5, E5, S5) |

### 5. Statistical Methods (4)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `stat_variance` | Local variance map | Smooth panels vs textured scenes | numpy sliding window variance |
| `stat_entropy` | Local entropy map | Region complexity measure | `skimage.filters.rank.entropy` |
| `stat_mahalanobis` | Mahalanobis color distance | Pixel classification into color clusters | numpy covariance + distance |
| `stat_mean_diff` | Adaptive mean color diff | Pixels differing from local average | numpy sliding window mean subtraction |

### 6. Gradient Analysis (3)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `grad_structure` | Structure tensor | Edge/corner/flat pixel classification | `skimage.feature.structure_tensor` |
| `grad_harris` | Harris corner detection | Border frame corners | `cv2.cornerHarris` |
| `grad_hog` | Oriented gradient histogram | Region type by gradient distribution | numpy cell-based histogram |

### 7. Structural Analysis (4)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `struct_contour` | Contour hierarchy | Nested contour tree (depth = UI signal) | `cv2.findContours` with RETR_TREE |
| `struct_ccl` | Connected component labeling | Region properties (area, rectangularity) | `cv2.connectedComponentsWithStats` |
| `struct_distance` | Distance transform | Border centerline and width | `cv2.distanceTransform` |
| `struct_watershed` | Watershed segmentation | Gradient-based region boundaries | `cv2.watershed` |

### 8. Adaptive & Frequency (4)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `adapt_sauvola` | Sauvola threshold | Borders under varying brightness | `skimage.filters.threshold_sauvola` |
| `adapt_niblack` | Niblack threshold | Alternative adaptive binarization | `skimage.filters.threshold_niblack` |
| `freq_fft_highpass` | FFT high-pass filter | Edge frequencies (removes background) | `numpy.fft.fft2` with high-pass mask |
| `freq_wavelet` | Wavelet multi-scale edges | Borders at multiple resolutions | `pywt.dwt2` or scipy wavelet |

### 9. Color Quantization & Grouping (3)

| ID | Technique | What It Detects | Implementation |
|----|-----------|-----------------|----------------|
| `quant_median` | Median cut quantization | Natural color boundaries (8-16 colors) | numpy histogram-based median cut |
| `quant_kmeans` | K-means color clustering | Border/panel/background pixel groups | `cv2.kmeans` |
| `quant_slic` | SLIC superpixel boundaries | Region borders between similar areas | `skimage.segmentation.slic` |

## Ensemble Logic

### Weighted Voting (v1)

Each technique produces a `border_confidence[y][x]` array (0.0-1.0).

```
final_border[y][x] = sum(technique_weight[i] * technique_output[i][y][x]) / sum(technique_weight[i])
```

Weights are normalized so they sum to 1.0. Default: all equal (1/40 each).

### Consensus Map

Independent of weights:
```
consensus[y][x] = count of techniques where output[y][x] > 0.5
```

Pixels where `consensus >= N` (configurable, default 10 of 40) are high-confidence borders.

### Final Border Map

```
final = max(weighted_ensemble, consensus_threshold_mask)
```

The final map takes the higher value — if weighted voting says "strong border" OR if 10+ techniques independently agree, it's a border.

### Thresholding

The returned border confidence map is continuous (0-255). The caller (`buildBlackBorderUiMask` in app.js) applies its own threshold as it does today with the gradient map.

## Calibration

### Weight Update Formula

After a test run against reference images:

```
For each technique i:
    score[i] = 0.4 * iou_vs_reference[i] + 0.3 * iou_vs_consensus[i] + 0.3 * iou_vs_v5plus[i]
    new_weight[i] = 0.7 * old_weight[i] + 0.3 * score[i]
```

- 70/30 EMA smoothing prevents wild swings from a single test run
- Techniques that consistently score well rise; poor performers sink
- No technique weight drops below 0.01 (floor) — every technique always contributes

### Calibration File Format

`tests/reports/border_calibration.json`:
```json
{
    "version": 1,
    "last_updated": "2026-03-30T16:00:00",
    "technique_weights": {
        "edge_sobel": 0.025,
        "edge_scharr": 0.025,
        ...
    },
    "technique_scores": {
        "edge_sobel": {
            "iou_vs_reference": 0.82,
            "iou_vs_consensus": 0.91,
            "iou_vs_v5plus": 0.78,
            "composite": 0.84
        },
        ...
    },
    "consensus_threshold": 10,
    "history": [
        {"date": "2026-03-30", "dark_iou": 0.95, "light_iou": 0.97}
    ]
}
```

## API Endpoint

### POST `/api/border-detect`

**Request body** (multipart or JSON with base64):
```json
{
    "image": "<base64 PNG>",
    "width": 1920,
    "height": 1080,
    "mode": "general",
    "reference_path": null,
    "v5_border_map": null
}
```

- `mode`: `"general"` (A+C) or `"test"` (D)
- `reference_path`: path to reference image (test mode only)
- `v5_border_map`: base64 PNG of current v5+ border detection (test mode only)

**Response** (general mode):
```json
{
    "border_map": "<base64 grayscale PNG>",
    "consensus_count": 14,
    "processing_ms": 2100,
    "techniques_run": 40
}
```

**Response** (test mode — adds diagnostic payload):
```json
{
    "border_map": "<base64 grayscale PNG>",
    "consensus_count": 14,
    "processing_ms": 2100,
    "techniques_run": 40,
    "diagnostics": {
        "technique_scores": { ... },
        "weight_changes": { ... },
        "agreement_map": "<base64 PNG>",
        "top_5": ["edge_canny", "morph_blackhat", "color_lab_delta", ...],
        "bottom_5": ["quant_median", "freq_wavelet", ...]
    }
}
```

## app.js Integration

In `buildBlackBorderUiMask()`, before the current gradient computation:

```javascript
// Try multi-spectrum border detection via server
let borderMap = null;
try {
    const response = await fetch('/api/border-detect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            image: canvasToBase64(sourceCanvas),
            width: W,
            height: H,
            mode: 'general'
        })
    });
    if (response.ok) {
        const result = await response.json();
        borderMap = base64ToImageData(result.border_map);
        console.log(`Multi-spectrum border detection: ${result.techniques_run} techniques, ${result.processing_ms}ms, consensus=${result.consensus_count}`);
    }
} catch (e) {
    console.log('Multi-spectrum unavailable, using v5+ fallback');
}

// Use multi-spectrum result or fall back to current gradient+achromatic
if (borderMap) {
    // Use borderMap as the border detection input
    // (replaces gradient + achromatic dual criteria)
} else {
    // Current v5+ gradient + achromatic detection (unchanged)
}
```

The rest of the v5+ pipeline (component labeling, background by variance, trapped bg, invert selection) works on whatever border map it receives.

## Skill Definition

`.claude/skills/border-detect/SKILL.md`:

The skill runs the diagnostic mode. Steps:
1. Check that serve.py is running (start if needed via server_manager)
2. Accept an image path or use the dark reference source image as default
3. Call `/api/border-detect` in test mode with reference images
4. Print ranked technique scorecard (all 40 techniques sorted by composite score)
5. Print technique agreement analysis (which techniques agree/disagree on which regions)
6. Print calibration weight changes (before vs after)
7. Print ensemble quality metrics (final border map IoU vs reference)
8. Save all artifacts (per-technique masks, agreement map, diff heatmaps) to `tests/reports/border_detect/`

## Performance Strategy

- **Parallel execution:** Use `concurrent.futures.ThreadPoolExecutor` to run independent techniques in parallel. Most techniques are CPU-bound numpy/opencv ops that release the GIL.
- **Integral images:** Pre-compute sum and sum-of-squares integral images once. All windowed statistics (variance, mean, entropy) become O(1) per pixel.
- **Shared preprocessing:** Convert to grayscale, HSV, LAB, YCbCr once. All techniques reuse the same converted images.
- **Downsample option:** For images >2MP, optionally run techniques on half-resolution, then upscale the border map. Configurable.

## Testing

- Unit tests for each technique category (mock images with known borders)
- Integration test via launcher: `/api/border-detect` endpoint responds and returns valid border map
- Production test integration: test mode runs during production loop, calibration file updates
- Performance test: all 40 techniques complete in <3 seconds on 1920x1080
