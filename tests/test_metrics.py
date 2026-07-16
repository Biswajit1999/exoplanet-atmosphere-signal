from __future__ import annotations

import numpy as np
import pytest

from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError
from jwst_wasp39b_evidence_ladder.metrics import aic, bic, evidence_ladder, weighted_chi_square


def test_weighted_chi_square_zero_for_perfect_model():
    data = np.array([1.0, 2.0, 3.0])
    assert weighted_chi_square(data, data, np.array([0.1, 0.1, 0.1])) == pytest.approx(0.0)


def test_weighted_chi_square_raises_on_empty():
    with pytest.raises(InsufficientDataError):
        weighted_chi_square(np.array([]), np.array([]), np.array([]))


def test_aic_bic_increase_with_chi_square():
    assert aic(10.0, 1) > aic(5.0, 1)
    assert bic(10.0, 1, 20) > bic(5.0, 1, 20)


def test_evidence_ladder_prefers_complex_when_it_fits_better():
    n = 50
    wl = np.linspace(4.0, 5.2, n)
    err = np.full(n, 0.0002)
    rng = np.random.default_rng(1)
    baseline = 0.020
    truth = baseline + 0.002 * np.exp(-0.5 * ((wl - 4.6) / 0.08) ** 2)
    data = truth + rng.normal(0.0, 0.0002, size=n)
    simple = np.full(n, baseline)
    result = evidence_ladder(data, err, simple, truth, n_params_simple=0, n_params_complex=1)
    assert result.preferred_model == "complex"
    assert result.delta_aic > 0
    assert result.delta_bic > 0


def test_evidence_ladder_prefers_simple_on_null_data():
    n = 50
    err = np.full(n, 0.0002)
    rng = np.random.default_rng(2)
    baseline = 0.020
    data = baseline + rng.normal(0.0, 0.0002, size=n)
    simple = np.full(n, baseline)
    complex_model = np.full(n, baseline)  # identical model: no benefit, extra param penalized
    result = evidence_ladder(data, err, simple, complex_model, n_params_simple=0, n_params_complex=1)
    assert result.preferred_model == "simple"


def test_evidence_ladder_raises_on_empty_data():
    with pytest.raises(InsufficientDataError):
        evidence_ladder(np.array([]), np.array([]), np.array([]), np.array([]), 0, 1)
