"""Morphological operation techniques (5)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("morph_gradient", _stub), ("morph_blackhat", _stub),
    ("morph_close_gaps", _stub), ("morph_tophat", _stub),
    ("morph_width_probe", _stub),
]
