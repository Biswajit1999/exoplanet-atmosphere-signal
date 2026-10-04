from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from jwst_wasp39b_evidence_ladder.config import (
    AnalysisConfig,
    ExecutionConfig,
    InputConfig,
    ProjectMeta,
    ProvenanceConfig,
    ValidationConfig,
)
from jwst_wasp39b_evidence_ladder.core import bootstrap_contrast, run_pipeline
from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError
from jwst_wasp39b_evidence_ladder.io import COSubBandSamples


def _dummy_config() -> AnalysisConfig:
    return AnalysisConfig(
        project=ProjectMeta(title="t", repository="r", author="a", curation_status="c", priority=1.0),
        execution=ExecutionConfig(seed=1, output_directory="results", overwrite=False, fail_on_warning=False),
        input=InputConfig(data_mode="real", manifest="data/manifest.csv", raw_directory="data/raw", example_directory="data/example"),
        validation=ValidationConfig(minimum_sample_size=1, bootstrap_resamples=500, confidence_level=0.95),
        provenance=ProvenanceConfig(record_environment=True, record_git_commit=True, verify_checksums=True),
    )


def test_run_pipeline_raises_on_empty_manifest():
    with pytest.raises(InsufficientDataError):
        run_pipeline([], Path("."), _dummy_config())


def test_run_pipeline_requires_both_analysis_products(tmp_path):
    result = run_pipeline([{"product_id": "unrelated"}], tmp_path, _dummy_config())
    assert result.target is None
    assert "manifest must include" in result.warnings[0]


def test_bootstrap_contrast_is_deterministic_and_contains_signal():
    samples = COSubBandSamples(
        wavelength_in_um=np.arange(20.0), depth_in=np.linspace(0.0202, 0.0204, 20),
        wavelength_out_um=np.arange(24.0), depth_out=np.linspace(0.0199, 0.0201, 24),
    )
    first = bootstrap_contrast(samples, n_resamples=500, seed=3)
    second = bootstrap_contrast(samples, n_resamples=500, seed=3)
    assert first == second
    assert first[0] > 0.0


def test_released_products_reproduce_published_co_contrast():
    root = Path(__file__).resolve().parents[1]
    manifest = [
        {"product_id": "wasp39b_grant2023_transmission_spectrum"},
        {"product_id": "wasp39b_grant2023_co_sub_band_samples"},
    ]
    result = run_pipeline(manifest, root / "data" / "raw", _dummy_config())
    assert result.target is not None
    assert result.target.contrast.n_in == 111
    assert result.target.contrast.n_out == 145
    assert result.target.contrast.contrast_ppm == pytest.approx(263.6595, abs=0.001)
    assert result.target.contrast.t_statistic == pytest.approx(3.89543, abs=1e-5)
    assert result.target.contrast.p_one_sided == pytest.approx(6.29586e-5, rel=1e-4)
