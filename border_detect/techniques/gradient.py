"""Gradient analysis techniques (3)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("grad_structure", _stub), ("grad_harris", _stub), ("grad_hog", _stub),
]
