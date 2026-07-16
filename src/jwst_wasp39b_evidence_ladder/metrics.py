"""Weighted chi-square, AIC, BIC and nested-model preference decision.

The "evidence ladder" central to this project's scientific question: for a
pair of nested models (fewer-parameter vs. more-parameter), report chi2,
AIC, BIC for each and which model is statistically preferred.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError


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
