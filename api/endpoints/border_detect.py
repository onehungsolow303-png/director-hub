"""Endpoint handler for /api/border-detect — full detection pipeline.

Runs v5+ invert-selection pipeline with multi-spectrum cleanup.
Returns a final alpha mask (not just a border map).
"""

import base64
import io
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from border_detect import detect_borders
from border_detect.pipeline import _multi_spectrum_cleanup
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

        start = time.time()

        # Load calibration weights
        weights = load_weights(CALIBRATION_PATH)

        # Run multi-spectrum ensemble to get border confidence map
        ensemble_result = detect_borders(img_bgr, mode=mode, calibration_weights=weights)

        # If a v5+ mask was provided (from JS Pass 1), run cleanup on it
        # Otherwise return just the border map for JS to use
        v5_mask_b64 = params.get("v5_mask")
        alpha_mask = None
        print(f"  [border-detect] v5_mask present: {v5_mask_b64 is not None and len(str(v5_mask_b64)) > 0}, params keys: {list(params.keys())}")
        if v5_mask_b64:
            try:
                v5_data = base64.b64decode(v5_mask_b64)
                v5_img = Image.open(io.BytesIO(v5_data)).convert("L")
                v5_alpha = np.array(v5_img)
                ms_map = ensemble_result["border_map"].astype(np.float32) / 255.0
                # Resize if needed
                if v5_alpha.shape[:2] != img_bgr.shape[:2]:
                    v5_alpha = cv2.resize(v5_alpha, (img_bgr.shape[1], img_bgr.shape[0]),
                                          interpolation=cv2.INTER_NEAREST)
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
                rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(np.float64)
                alpha_mask = _multi_spectrum_cleanup(v5_alpha, ms_map, rgb, gray, img_bgr.shape[0], img_bgr.shape[1])
            except Exception as e:
                print(f"  Cleanup failed: {e}")
                import traceback; traceback.print_exc()

        elapsed_ms = (time.time() - start) * 1000

        # Encode border map
        _, border_png = cv2.imencode(".png", ensemble_result["border_map"])
        border_b64 = base64.b64encode(border_png.tobytes()).decode()

        response = {
            "border_map": border_b64,
            "techniques_run": ensemble_result["techniques_run"],
            "processing_ms": round(elapsed_ms, 1),
            "consensus_count": ensemble_result["consensus_count"],
        }

        # Add cleaned mask if cleanup was performed
        if alpha_mask is not None:
            _, mask_png = cv2.imencode(".png", alpha_mask)
            response["cleaned_mask"] = base64.b64encode(mask_png.tobytes()).decode()
            response["pipeline"] = "v5+ms_cleanup"
        else:
            response["pipeline"] = "ensemble_only"

        # Test mode: add diagnostics and update calibration
        if mode == "test" and "per_technique" in ensemble_result:
            reference_path = params.get("reference_path")
            v5_border_map_b64 = params.get("v5_border_map")

            diagnostics = _build_diagnostics(
                ensemble_result["per_technique"], ensemble_result["border_map"],
                reference_path, v5_border_map_b64, weights
            )
            response["diagnostics"] = diagnostics

            if diagnostics.get("technique_scores"):
                save_calibration(CALIBRATION_PATH, diagnostics["technique_scores"], weights)

        return 200, response

    return _handler


def _build_diagnostics(per_technique, final_map, reference_path, v5_b64, current_weights):
    """Build diagnostic payload for test mode."""
    diagnostics = {"technique_scores": {}, "weight_changes": {}}

    ref_mask = None
    if reference_path:
        try:
            ref_img = Image.open(reference_path).convert("L")
            ref_mask = np.array(ref_img)
        except Exception:
            pass

    v5_mask = None
    if v5_b64:
        try:
            v5_data = base64.b64decode(v5_b64)
            v5_img = Image.open(io.BytesIO(v5_data)).convert("L")
            v5_mask = np.array(v5_img)
        except Exception:
            pass

    h, w = final_map.shape[:2]

    if ref_mask is not None and ref_mask.shape[:2] != (h, w):
        ref_mask = cv2.resize(ref_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    if v5_mask is not None and v5_mask.shape[:2] != (h, w):
        v5_mask = cv2.resize(v5_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    consensus = np.zeros((h, w), dtype=np.int32)
    for output in per_technique.values():
        consensus += (output > 0.5).astype(np.int32)
    consensus_binary = (consensus >= max(1, len(per_technique) // 4)).astype(np.uint8) * 255

    for tid, output in per_technique.items():
        binary = (output > 0.5).astype(np.uint8) * 255
        scores = {}
        if ref_mask is not None:
            scores["iou_vs_reference"] = _iou(binary, ref_mask)
        if v5_mask is not None:
            scores["iou_vs_v5plus"] = _iou(binary, v5_mask)
        scores["iou_vs_consensus"] = _iou(binary, consensus_binary)
        vals = list(scores.values())
        scores["composite"] = sum(vals) / len(vals) if vals else 0.0
        diagnostics["technique_scores"][tid] = scores

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
