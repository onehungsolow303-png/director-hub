"""Ensemble combiner — weighted voting + consensus for border detection."""
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from border_detect.preprocess import preprocess
from border_detect.techniques import get_all_techniques

def detect_borders(img_bgr, mode="general", calibration_weights=None):
    start = time.time()
    preprocessed = preprocess(img_bgr)
    techniques = get_all_techniques()
    h, w = preprocessed["height"], preprocessed["width"]
    results = {}
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(_run_one, tid, fn, preprocessed): tid for tid, fn in techniques}
        for future in futures:
            tid = futures[future]
            try:
                results[tid] = future.result(timeout=10)
            except Exception as e:
                print(f"  Technique {tid} failed: {e}")
                results[tid] = np.zeros((h, w), dtype=np.float32)
    if calibration_weights is None:
        calibration_weights = {}
    default_weight = 1.0 / len(techniques)
    weights = {tid: calibration_weights.get(tid, default_weight) for tid, _ in techniques}
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
    consensus = np.zeros((h, w), dtype=np.int32)
    for output in results.values():
        consensus += (output > 0.5).astype(np.int32)
    consensus_threshold = max(1, len(techniques) // 4)
    consensus_mask = (consensus >= consensus_threshold).astype(np.float64)
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
    output = fn(preprocessed)
    if output.dtype == np.uint8:
        output = output.astype(np.float32) / 255.0
    return np.clip(output, 0.0, 1.0).astype(np.float32)
