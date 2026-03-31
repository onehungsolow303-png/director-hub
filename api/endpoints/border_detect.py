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

    # Resize reference and v5 masks to match detection output dimensions
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
