from __future__ import annotations

import numpy as np
import pytest

from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError
from jwst_wasp39b_evidence_ladder.fitting import fit_flat, fit_flat_plus_gaussian
from jwst_wasp39b_evidence_ladder.models import flat_model, flat_plus_gaussian_model


def test_flat_model_is_constant():
    wl = np.linspace(4.0, 5.2, 10)
    out = flat_model(wl, baseline=0.02)
    assert np.allclose(out, 0.02)


def test_flat_plus_gaussian_peaks_at_center():
    wl = np.linspace(4.0, 5.2, 200)
    out = flat_plus_gaussian_model(wl, baseline=0.02, amplitude=0.001, center_um=4.6, width_um=0.08)
    peak_wl = wl[np.argmax(out)]
    assert abs(peak_wl - 4.6) < 0.02


def test_fit_flat_recovers_baseline(synthetic_spectrum_null):
    s = synthetic_spectrum_null
    result = fit_flat(s.wavelength_um, s.transit_depth, s.transit_depth_err)
    assert abs(result.params[0] - 0.020) < 0.001


def test_fit_flat_plus_gaussian_recovers_injected_amplitude(synthetic_spectrum_with_feature):
    s = synthetic_spectrum_with_feature
    result = fit_flat_plus_gaussian(s.wavelength_um, s.transit_depth, s.transit_depth_err, center0=4.6)
    recovered_amplitude = result.params[1]
    assert abs(recovered_amplitude - s.truth_amplitude) < 0.0005


def test_fit_flat_raises_on_too_few_points():
    with pytest.raises(InsufficientDataError):
        fit_flat(np.array([4.5]), np.array([0.02]), np.array([0.0002]))
