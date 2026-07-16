"""Synthetic transmission-spectrum generator with a known injected Gaussian
absorption feature (or none, for the null-control direction), used for the
required injection-recovery validation gate.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jwst_wasp39b_evidence_ladder.models import flat_model, flat_plus_gaussian_model


@dataclass(frozen=True)
class SyntheticSpectrumSpec:
    n_points: int = 60
    wavelength_min_um: float = 4.0
    wavelength_max_um: float = 5.2
    baseline: float = 0.020
    noise_sigma: float = 0.0002
    feature_amplitude: float = 0.0015
    feature_center_um: float = 4.6
    feature_width_um: float = 0.08


@dataclass(frozen=True)
class SyntheticSpectrum:
    wavelength_um: np.ndarray
    transit_depth: np.ndarray
    transit_depth_err: np.ndarray
    truth_amplitude: float
    truth_center_um: float
    truth_width_um: float


def make_synthetic_spectrum(
    spec: SyntheticSpectrumSpec = SyntheticSpectrumSpec(), seed: int = 20260713, inject_feature: bool = True
) -> SyntheticSpectrum:
    """Generate a synthetic transmission spectrum with (or without, for the
    null-control test) a known injected Gaussian absorption feature.
    """
    rng = np.random.default_rng(seed)
    wavelength = np.linspace(spec.wavelength_min_um, spec.wavelength_max_um, spec.n_points)
    err = np.full(spec.n_points, spec.noise_sigma)

    if inject_feature:
        truth = flat_plus_gaussian_model(
            wavelength, spec.baseline, spec.feature_amplitude, spec.feature_center_um, spec.feature_width_um
        )
        amplitude, center, width = spec.feature_amplitude, spec.feature_center_um, spec.feature_width_um
    else:
        truth = flat_model(wavelength, spec.baseline)
        amplitude, center, width = 0.0, spec.feature_center_um, spec.feature_width_um

    depth = truth + rng.normal(0.0, spec.noise_sigma, size=spec.n_points)
    return SyntheticSpectrum(
        wavelength_um=wavelength, transit_depth=depth, transit_depth_err=err,
        truth_amplitude=amplitude, truth_center_um=center, truth_width_um=width,
    )
