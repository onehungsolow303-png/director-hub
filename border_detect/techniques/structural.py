"""Structural analysis techniques (4)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("struct_contour", _stub), ("struct_ccl", _stub),
    ("struct_distance", _stub), ("struct_watershed", _stub),
]
