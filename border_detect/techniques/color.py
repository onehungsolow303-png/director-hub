"""Color-space analysis techniques (5)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("color_hsv_dark", _stub), ("color_lab_delta", _stub),
    ("color_ycbcr_luma", _stub), ("color_rgb_gradient", _stub),
    ("color_achromatic", _stub),
]
