"""Adaptive thresholding & frequency domain techniques (4)."""
import numpy as np

def _stub(preprocessed):
    h, w = preprocessed["height"], preprocessed["width"]
    return np.zeros((h, w), dtype=np.float32)

TECHNIQUES = [
    ("adapt_sauvola", _stub), ("adapt_niblack", _stub),
    ("freq_fft_highpass", _stub), ("freq_wavelet", _stub),
]
