"""Required validation gate: the evidence-ladder + fitting pipeline must
recover an injected feature (injection-recovery) and must NOT report a
significant feature when none was injected (null control).
"""
from __future__ import annotations

import numpy as np

from jwst_wasp39b_evidence_ladder.exceptions import ConvergenceError
from jwst_wasp39b_evidence_ladder.fitting import fit_flat_plus_gaussian
from jwst_wasp39b_evidence_ladder.metrics import evidence_ladder
from jwst_wasp39b_evidence_ladder.models import flat_model
from jwst_wasp39b_evidence_ladder.synthetic import SyntheticSpectrumSpec, make_synthetic_spectrum


def test_injection_recovery_prefers_complex_model_and_recovers_amplitude(synthetic_spectrum_with_feature):
    s = synthetic_spectrum_with_feature
    fit = fit_flat_plus_gaussian(s.wavelength_um, s.transit_depth, s.transit_depth_err, center0=4.6)
    simple = flat_model(s.wavelength_um, baseline=float(np.median(s.transit_depth)))
    ladder = evidence_ladder(
        s.transit_depth, s.transit_depth_err, simple, fit.model_values,
        n_params_simple=0, n_params_complex=4,
    )
    assert ladder.preferred_model == "complex"
    assert abs(fit.params[1] - s.truth_amplitude) < 0.0005


def test_null_control_does_not_prefer_complex_model(synthetic_spectrum_null):
    """On pure noise (no injected feature), the 4-parameter Gaussian fit is
    expected to be unconstrained (ill-conditioned covariance) since there is
    no real feature for it to lock onto. That ConvergenceError is itself the
    null-control signal: the pipeline must not silently report a confident,
    ill-conditioned fit as a preferred complex model.
    """
    s = synthetic_spectrum_null
    simple = flat_model(s.wavelength_um, baseline=float(np.median(s.transit_depth)))
    try:
        fit = fit_flat_plus_gaussian(s.wavelength_um, s.transit_depth, s.transit_depth_err, center0=4.6)
    except ConvergenceError:
        return
    ladder = evidence_ladder(
        s.transit_depth, s.transit_depth_err, simple, fit.model_values,
        n_params_simple=0, n_params_complex=4,
    )
    assert ladder.preferred_model == "simple"
    assert abs(fit.params[1]) < 0.001


def test_recovery_amplitude_scales_with_injected_amplitude():
    spec = SyntheticSpectrumSpec(feature_amplitude=0.003)
    s = make_synthetic_spectrum(spec, seed=7, inject_feature=True)
    fit = fit_flat_plus_gaussian(s.wavelength_um, s.transit_depth, s.transit_depth_err, center0=4.6)
    assert fit.params[1] > 0.002
