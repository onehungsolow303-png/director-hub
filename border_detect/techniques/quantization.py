"""Color quantization & grouping techniques (3)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("quant_median", _stub), ("quant_kmeans", _stub), ("quant_slic", _stub),
]
