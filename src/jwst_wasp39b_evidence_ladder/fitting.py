"""Weighted least-squares fitting of models.py models to a spectrum, used
for the synthetic injection-recovery validation gate.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from jwst_wasp39b_evidence_ladder.exceptions import ConvergenceError, InsufficientDataError
from jwst_wasp39b_evidence_ladder.models import flat_plus_gaussian_model, flat_model
from jwst_wasp39b_evidence_ladder.uncertainty import check_fit_convergence


@dataclass(frozen=True)
class FitResult:
    params: np.ndarray
    covariance: np.ndarray
    model_values: np.ndarray


def fit_flat(wavelength: np.ndarray, depth: np.ndarray, depth_err: np.ndarray) -> FitResult:
    if wavelength.size < 2:
        raise InsufficientDataError("fit_flat requires at least 2 points")
    baseline0 = float(np.average(depth, weights=1.0 / depth_err**2))
    popt, pcov = curve_fit(flat_model, wavelength, depth, p0=[baseline0], sigma=depth_err, absolute_sigma=True)
    residuals = depth - flat_model(wavelength, *popt)
    dof = wavelength.size - 1
    check_fit_convergence(pcov, residuals=residuals / depth_err, dof=dof)
    return FitResult(params=popt, covariance=pcov, model_values=flat_model(wavelength, *popt))


def fit_flat_plus_gaussian(
    wavelength: np.ndarray, depth: np.ndarray, depth_err: np.ndarray,
    center0: float, width0: float = 0.05,
) -> FitResult:
    if wavelength.size < 4:
        raise InsufficientDataError("fit_flat_plus_gaussian requires at least 4 points")
    baseline0 = float(np.median(depth))
    amplitude0 = float(np.max(depth) - baseline0)
    p0 = [baseline0, amplitude0, center0, width0]
    bounds = ([-np.inf, -np.inf, wavelength.min(), 1e-4], [np.inf, np.inf, wavelength.max(), 10.0])
    try:
        popt, pcov = curve_fit(
            flat_plus_gaussian_model, wavelength, depth, p0=p0, sigma=depth_err, absolute_sigma=True, bounds=bounds, maxfev=10000
        )
    except RuntimeError as exc:
        raise ConvergenceError(f"fit_flat_plus_gaussian did not converge: {exc}") from exc
    residuals = depth - flat_plus_gaussian_model(wavelength, *popt)
    dof = wavelength.size - 4
    if dof > 0:
        check_fit_convergence(pcov, residuals=residuals / depth_err, dof=dof)
    else:
        check_fit_convergence(pcov)
    return FitResult(params=popt, covariance=pcov, model_values=flat_plus_gaussian_model(wavelength, *popt))
