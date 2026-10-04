"""Statistical estimands used by the reproducible CO sub-band analysis."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError


@dataclass(frozen=True)
class WelchContrast:
    n_in: int
    n_out: int
    mean_in_ppm: float
    mean_out_ppm: float
    contrast_ppm: float
    standard_error_ppm: float
    t_statistic: float
    degrees_of_freedom: float
    p_one_sided: float
    ci95_low_ppm: float
    ci95_high_ppm: float


def welch_sub_band_contrast(depth_in: np.ndarray, depth_out: np.ndarray) -> WelchContrast:
    """Difference of means and one-sided Welch test, expressed in ppm.

    The alternative is the preregistered physical direction used in Grant et al.:
    the CO-selected sub-bands have greater transit depth than the comparison bands.
    """
    inside = np.asarray(depth_in, dtype=float)
    outside = np.asarray(depth_out, dtype=float)
    if inside.size < 2 or outside.size < 2:
        raise InsufficientDataError("Welch contrast requires at least two samples per group")
    if not np.all(np.isfinite(inside)) or not np.all(np.isfinite(outside)):
        raise InsufficientDataError("Welch contrast received non-finite data")
    inside_ppm, outside_ppm = inside * 1e6, outside * 1e6
    vi, vo = np.var(inside_ppm, ddof=1), np.var(outside_ppm, ddof=1)
    ni, no = inside_ppm.size, outside_ppm.size
    se2_i, se2_o = vi / ni, vo / no
    se = float(np.sqrt(se2_i + se2_o))
    dof = float((se2_i + se2_o) ** 2 / (se2_i**2 / (ni - 1) + se2_o**2 / (no - 1)))
    contrast = float(np.mean(inside_ppm) - np.mean(outside_ppm))
    t_stat = contrast / se
    critical = float(stats.t.ppf(0.975, dof))
    return WelchContrast(
        n_in=int(ni), n_out=int(no), mean_in_ppm=float(np.mean(inside_ppm)),
        mean_out_ppm=float(np.mean(outside_ppm)), contrast_ppm=contrast,
        standard_error_ppm=se, t_statistic=t_stat, degrees_of_freedom=dof,
        p_one_sided=float(stats.t.sf(t_stat, dof)),
        ci95_low_ppm=contrast - critical * se, ci95_high_ppm=contrast + critical * se,
    )


@dataclass(frozen=True)
class FixedCurveDiagnostic:
    n_points: int
    chi2_no_co: float
    chi2_full: float
    delta_chi2: float
    chi2_per_point_no_co: float
    chi2_per_point_full: float


def fixed_curve_diagnostic(
    data: np.ndarray, uncertainty: np.ndarray, model_no_co: np.ndarray, model_full: np.ndarray,
) -> FixedCurveDiagnostic:
    """Goodness-of-fit comparison for two archived curves that were not refit here.

    No AIC/BIC is calculated: the release does not encode the fitted parameter
    counts or likelihood construction needed for a valid information criterion.
    """
    n = int(np.asarray(data).size)
    if n == 0:
        raise InsufficientDataError("fixed_curve_diagnostic: empty data array")
    no_co = weighted_chi_square(data, model_no_co, uncertainty)
    full = weighted_chi_square(data, model_full, uncertainty)
    return FixedCurveDiagnostic(n, no_co, full, no_co - full, no_co / n, full / n)


def weighted_chi_square(data: np.ndarray, model: np.ndarray, uncertainty: np.ndarray) -> float:
    data = np.asarray(data, dtype=float)
    model = np.asarray(model, dtype=float)
    uncertainty = np.asarray(uncertainty, dtype=float)
    if data.size == 0:
        raise InsufficientDataError("weighted_chi_square: empty data array")
    return float(np.sum(((data - model) / uncertainty) ** 2))


def aic(chi_square: float, n_params: int) -> float:
    """Akaike Information Criterion, Gaussian-likelihood form."""
    return chi_square + 2.0 * n_params


def bic(chi_square: float, n_params: int, n_points: int) -> float:
    """Bayesian Information Criterion, Gaussian-likelihood form."""
    return chi_square + n_params * np.log(n_points)


@dataclass(frozen=True)
class EvidenceLadderResult:
    chi2_simple: float
    chi2_complex: float
    aic_simple: float
    aic_complex: float
    bic_simple: float
    bic_complex: float
    delta_aic: float  # aic_simple - aic_complex; positive favours the complex model
    delta_bic: float
    preferred_model: str  # "simple" or "complex"


def evidence_ladder(
    data: np.ndarray, uncertainty: np.ndarray,
    model_simple: np.ndarray, model_complex: np.ndarray,
    n_params_simple: int, n_params_complex: int,
) -> EvidenceLadderResult:
    """Compare a simple (fewer-parameter) and complex (more-parameter,
    nested) model via chi-square/AIC/BIC.

    By convention (Jeffreys/Kass-Raftery scale, commonly applied to
    Delta-AIC/BIC): Delta > ~2 is "positive" evidence, Delta > ~6 is
    "strong" evidence for the complex model; this function reports the
    raw deltas and a simple preferred_model decision (complex model
    preferred iff its AIC AND BIC are both lower), leaving strength-of-evidence
    interpretation to the caller/report.
    """
    n_points = np.asarray(data).size
    if n_points == 0:
        raise InsufficientDataError("evidence_ladder: empty data array")

    chi2_s = weighted_chi_square(data, model_simple, uncertainty)
    chi2_c = weighted_chi_square(data, model_complex, uncertainty)
    aic_s = aic(chi2_s, n_params_simple)
    aic_c = aic(chi2_c, n_params_complex)
    bic_s = bic(chi2_s, n_params_simple, n_points)
    bic_c = bic(chi2_c, n_params_complex, n_points)

    delta_aic = aic_s - aic_c
    delta_bic = bic_s - bic_c
    preferred = "complex" if (aic_c < aic_s and bic_c < bic_s) else "simple"

    return EvidenceLadderResult(
        chi2_simple=chi2_s, chi2_complex=chi2_c,
        aic_simple=aic_s, aic_complex=aic_c,
        bic_simple=bic_s, bic_complex=bic_c,
        delta_aic=delta_aic, delta_bic=delta_bic,
        preferred_model=preferred,
    )
