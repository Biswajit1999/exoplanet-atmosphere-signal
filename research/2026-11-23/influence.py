"""Conditional weighted spectral-regression influence diagnostics (synthetic/derived)."""
import numpy as np

def _inputs(x, y, sigma):
    x, y, sigma = (np.asarray(a, dtype=float) for a in (x, y, sigma))
    if x.ndim != 2 or y.shape != (len(x),) or sigma.shape != y.shape:
        raise ValueError("incompatible dimensions")
    if len(y) <= x.shape[1] + 1 or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("insufficient or nonfinite data")
    if not np.all(np.isfinite(sigma)) or np.any(sigma <= 0):
        raise ValueError("uncertainties must be positive")
    if np.linalg.matrix_rank(x / sigma[:, None]) < x.shape[1]:
        raise ValueError("rank-deficient design")
    return x, y, sigma

def weighted_fit(x, y, sigma):
    """QR-based weighted linear fit; formal covariance assumes independent known errors."""
    x, y, sigma = _inputs(x, y, sigma)
    a = x / sigma[:, None]
    q, r = np.linalg.qr(a, mode="reduced")
    beta = np.linalg.solve(r, q.T @ (y / sigma))
    cov = np.linalg.solve(r, np.linalg.solve(r.T, np.eye(r.shape[0]))).T
    return beta, cov

def influence(x, y, sigma):
    """Exact leave-one-bin-out parameter shifts and weighted leverages."""
    x, y, sigma = _inputs(x, y, sigma)
    beta, _ = weighted_fit(x, y, sigma)
    a = x / sigma[:, None]
    q, _ = np.linalg.qr(a, mode="reduced")
    leverage = np.sum(q*q, axis=1)
    shifts = np.full((len(y), x.shape[1]), np.nan)
    for i in range(len(y)):
        keep = np.arange(len(y)) != i
        try:
            shifts[i] = weighted_fit(x[keep], y[keep], sigma[keep])[0] - beta
        except ValueError:
            pass
    return leverage, shifts

def block_deletion(x, y, sigma, wavelength, width):
    """Delete each occupied fixed-width wavelength block and refit."""
    x, y, sigma = _inputs(x, y, sigma)
    wave = np.asarray(wavelength, dtype=float)
    if wave.shape != y.shape or not np.all(np.isfinite(wave)) or width <= 0 or not np.isfinite(width):
        raise ValueError("invalid wavelength or width")
    baseline, _ = weighted_fit(x, y, sigma)
    bins = np.floor((wave - wave.min()) / width).astype(int)
    out = []
    for b in np.unique(bins):
        keep = bins != b
        try:
            delta = weighted_fit(x[keep], y[keep], sigma[keep])[0] - baseline
        except ValueError:
            delta = np.full(x.shape[1], np.nan)
        out.append((int(b), int(np.sum(~keep)), delta))
    return out
