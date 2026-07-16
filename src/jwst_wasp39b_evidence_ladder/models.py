"""Simple parametric spectrum models: flat continuum, and flat continuum
plus a single Gaussian absorption feature.

Used for the synthetic injection-recovery validation gate. Real-data
evidence-ladder comparisons use the real paper's own published full/no-CO
models directly (io.py), not these -- these are the "nested pair" for the
synthetic gate only.
"""
from __future__ import annotations

import numpy as np


def flat_model(wavelength: np.ndarray, baseline: float) -> np.ndarray:
    """Constant transit-depth model (no absorption feature)."""
    return np.full_like(np.asarray(wavelength, dtype=float), baseline)


def flat_plus_gaussian_model(
    wavelength: np.ndarray, baseline: float, amplitude: float, center_um: float, width_um: float
) -> np.ndarray:
    """Constant transit depth plus a single Gaussian absorption feature."""
    wl = np.asarray(wavelength, dtype=float)
    return baseline + amplitude * np.exp(-0.5 * ((wl - center_um) / width_um) ** 2)
