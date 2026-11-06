"""Conditional spectral-template inference; synthetic tests, not WASP-39 b data.

Model y = a*t + Gaussian noise with known positive-definite covariance.
All amplitudes are in the units of the supplied spectrum.
"""
import numpy as np


def ar1_covariance(n, sigma, rho):
    """Stationary AR(1) covariance C_ij = sigma^2 rho^|i-j|."""
    if n < 2 or sigma <= 0 or not -1 < rho < 1:
        raise ValueError("Need n>=2, sigma>0 and |rho|<1")
    idx = np.arange(n)
    return sigma**2 * rho**np.abs(idx[:, None] - idx[None, :])


def template_gls(signal, template, covariance):
    """Return GLS amplitude, its known-covariance 1-sigma error, and chi-square."""
    y = np.asarray(signal, dtype=float)
    t = np.asarray(template, dtype=float)
    c = np.asarray(covariance, dtype=float)
    if y.ndim != 1 or y.shape != t.shape or c.shape != (y.size, y.size):
        raise ValueError("Incompatible dimensions")
    if not (np.isfinite(y).all() and np.isfinite(t).all() and np.isfinite(c).all()):
        raise ValueError("Non-finite inputs")
    if not np.allclose(c, c.T, atol=1e-12, rtol=1e-12):
        raise ValueError("Covariance must be symmetric")
    try:
        l = np.linalg.cholesky(c)
        yw = np.linalg.solve(l, y)
        tw = np.linalg.solve(l, t)
    except np.linalg.LinAlgError as exc:
        raise ValueError("Covariance must be positive definite") from exc
    information = float(tw @ tw)
    if information <= 0:
        raise ValueError("Template must have nonzero information")
    amplitude = float(tw @ yw / information)
    residual = yw - amplitude * tw
    return amplitude, information**-0.5, float(residual @ residual)


def rho_sensitivity(signal, template, sigma, rhos):
    """Evaluate identical measurements under explicitly hypothetical AR(1) correlations."""
    return [{"rho": float(r), "amplitude": a, "sigma_amplitude": s, "chi2": chi2}
            for r in rhos
            for a, s, chi2 in [template_gls(signal, template,
                                           ar1_covariance(len(signal), sigma, r))]]


def injection_coverage(template, covariance, amplitude=1.0, draws=1000, seed=7):
    """Seeded known-template injection; empirical 68.27% normal-interval coverage."""
    if draws < 2:
        raise ValueError("At least two realizations required")
    t = np.asarray(template, dtype=float)
    c = np.asarray(covariance, dtype=float)
    l = np.linalg.cholesky(c)
    rng = np.random.default_rng(seed)
    estimates = np.array([template_gls(amplitude*t + l @ rng.standard_normal(t.size),
                                       t, c)[0] for _ in range(draws)])
    _, standard_error, _ = template_gls(amplitude*t, t, c)
    return {"draws": draws, "seed": seed, "bias": float(np.mean(estimates)-amplitude),
            "empirical_sd": float(np.std(estimates, ddof=1)),
            "analytic_sd": standard_error,
            "one_sigma_coverage": float(np.mean(np.abs(estimates-amplitude) <= standard_error))}
