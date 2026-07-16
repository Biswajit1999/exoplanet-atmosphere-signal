from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from jwst_wasp39b_evidence_ladder.config import AnalysisConfig, ExecutionConfig, InputConfig, ProjectMeta, ProvenanceConfig, ValidationConfig
from jwst_wasp39b_evidence_ladder.core import _feature_amplitude_bootstrap, run_pipeline
from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError
from jwst_wasp39b_evidence_ladder.io import WASP39bSpectrum


def _dummy_config() -> AnalysisConfig:
    return AnalysisConfig(
        project=ProjectMeta(title="t", repository="r", author="a", curation_status="c", priority=1.0),
        execution=ExecutionConfig(seed=1, output_directory="results", overwrite=False, fail_on_warning=False),
        input=InputConfig(data_mode="real", manifest="data/manifest.csv", raw_directory="data/raw", example_directory="data/example"),
        validation=ValidationConfig(minimum_sample_size=1, bootstrap_resamples=1000, confidence_level=0.95),
        provenance=ProvenanceConfig(record_environment=True, record_git_commit=True, verify_checksums=True),
    )


def test_run_pipeline_raises_on_empty_manifest():
    with pytest.raises(InsufficientDataError):
        run_pipeline([], Path("."), _dummy_config())


def test_run_pipeline_warns_and_returns_none_target_on_missing_file(tmp_path):
    manifest_rows = [{"product_id": "does_not_exist"}]
    result = run_pipeline(manifest_rows, tmp_path, _dummy_config())
    assert result.target is None
    assert any("skipped" in w for w in result.warnings)


def test_feature_amplitude_bootstrap_raises_when_co_band_too_small():
    n = 10
    wl = np.linspace(4.0, 5.2, n)
    spectrum = WASP39bSpectrum(
        wavelength_um=wl, transit_depth=np.full(n, 0.02), transit_depth_err=np.full(n, 0.0002),
        model_full=np.full(n, 0.02), model_no_feature=np.full(n, 0.02),
        model_feature_only=np.zeros(n),  # everything below the 10%-of-peak threshold
    )
    with pytest.raises(InsufficientDataError):
        _feature_amplitude_bootstrap(spectrum)


def test_feature_amplitude_bootstrap_recovers_null_near_zero():
    n = 60
    wl = np.linspace(4.0, 5.2, n)
    rng = np.random.default_rng(3)
    err = np.full(n, 0.0002)
    depth = 0.02 + rng.normal(0.0, 0.0002, size=n)
    feature_only = np.exp(-0.5 * ((wl - 4.6) / 0.08) ** 2)  # nonzero band, no real signal in data
    spectrum = WASP39bSpectrum(
        wavelength_um=wl, transit_depth=depth, transit_depth_err=err,
        model_full=np.full(n, 0.02), model_no_feature=np.full(n, 0.02),
        model_feature_only=feature_only,
    )
    ci_lo, ci_hi = _feature_amplitude_bootstrap(spectrum)
    assert ci_lo < 0.001 and ci_hi > -0.001
