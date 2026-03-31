"""Texture analysis techniques (4)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("tex_lbp", _stub), ("tex_gabor", _stub),
    ("tex_glcm", _stub), ("tex_laws", _stub),
]
