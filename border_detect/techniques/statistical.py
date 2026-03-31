"""Statistical method techniques (4)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("stat_variance", _stub), ("stat_entropy", _stub),
    ("stat_mahalanobis", _stub), ("stat_mean_diff", _stub),
]
