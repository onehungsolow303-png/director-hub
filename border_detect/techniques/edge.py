"""Edge detection techniques (8)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("edge_sobel", _stub), ("edge_scharr", _stub), ("edge_prewitt", _stub),
    ("edge_roberts", _stub), ("edge_log", _stub), ("edge_dog", _stub),
    ("edge_canny", _stub), ("edge_phase", _stub),
]
