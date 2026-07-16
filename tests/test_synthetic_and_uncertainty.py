from __future__ import annotations

import numpy as np
import pytest

from jwst_wasp39b_evidence_ladder.exceptions import ConvergenceError, InsufficientDataError
from jwst_wasp39b_evidence_ladder.synthetic import SyntheticSpectrumSpec, make_synthetic_spectrum
from jwst_wasp39b_evidence_ladder.uncertainty import bootstrap_statistic, check_fit_convergence


def test_synthetic_null_control_has_no_injected_feature():
    spec = SyntheticSpectrumSpec()
    s = make_synthetic_spectrum(spec, seed=1, inject_feature=False)
    assert s.truth_amplitude == 0.0


def test_synthetic_injected_feature_has_expected_truth():
    spec = SyntheticSpectrumSpec()
    s = make_synthetic_spectrum(spec, seed=1, inject_feature=True)
    assert s.truth_amplitude == spec.feature_amplitude
    assert s.truth_center_um == spec.feature_center_um


def test_synthetic_is_deterministic_for_fixed_seed():
    spec = SyntheticSpectrumSpec()
    a = make_synthetic_spectrum(spec, seed=42, inject_feature=True)
    b = make_synthetic_spectrum(spec, seed=42, inject_feature=True)
    assert np.array_equal(a.transit_depth, b.transit_depth)


def test_bootstrap_statistic_ci_contains_estimate():
    rng = np.random.default_rng(0)
    values = rng.normal(0.0, 1.0, size=200)
    result = bootstrap_statistic(values, statistic=np.mean, seed=0)
    assert result.ci_low <= result.estimate <= result.ci_high


def test_bootstrap_statistic_raises_on_insufficient_data():
    with pytest.raises(InsufficientDataError):
        bootstrap_statistic(np.array([1.0]))


def test_check_fit_convergence_raises_on_non_finite_covariance():
    cov = np.array([[np.inf, 0.0], [0.0, 1.0]])
    with pytest.raises(ConvergenceError):
        check_fit_convergence(cov)


def test_check_fit_convergence_raises_on_ill_conditioned_covariance():
    cov = np.array([[1e20, 0.0], [0.0, 1e-20]])
    with pytest.raises(ConvergenceError):
        check_fit_convergence(cov, max_condition_number=1e10)


def test_check_fit_convergence_passes_well_conditioned_covariance():
    cov = np.eye(2)
    result = check_fit_convergence(cov)
    assert result.converged
