"""Pipeline orchestration: real-data evidence-ladder comparison, bootstrap
feature-amplitude stability, leave-one-segment-out sensitivity, plus the
retained starter smoke-test functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from jwst_wasp39b_evidence_ladder.config import AnalysisConfig
from jwst_wasp39b_evidence_ladder.exceptions import (
    ConvergenceError,
    DataSchemaError,
    InsufficientDataError,
)
from jwst_wasp39b_evidence_ladder.io import WASP39bSpectrum, load_spectrum
from jwst_wasp39b_evidence_ladder.metrics import EvidenceLadderResult, evidence_ladder
from jwst_wasp39b_evidence_ladder.uncertainty import bootstrap_statistic


@dataclass(frozen=True)
class Summary:
    count: int
    median: float
    mad: float


def validate_numeric(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be one-dimensional")
    if arr.size == 0:
        raise ValueError("values must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("values contain non-finite entries")
    return arr


def robust_summary(values: np.ndarray) -> Summary:
    arr = validate_numeric(values)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return Summary(count=int(arr.size), median=median, mad=mad)


def demo_series(seed: int = 20260713, size: int = 128) -> np.ndarray:
    """Return deterministic synthetic data labelled only for smoke testing."""
    if size < 8:
        raise ValueError("size must be at least 8")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=size)


# The real published models are physically-motivated atmospheric retrieval
# fits, not simple analytic functions with an exactly-known free-parameter
# count from the netCDF file alone. Per docs/RESEARCH_BLUEPRINT.md's
# "simple nested-model" framing, this project treats the no-CO -> full-model
# step as adding exactly 1 effective parameter (the CO abundance/opacity
# term) -- a documented, defensible simplification, not a fabricated exact
# count from the original retrieval. See report.tex Limitations.
N_PARAMS_SIMPLE = 0
N_PARAMS_COMPLEX = 1

N_SEGMENTS = 3


@dataclass
class TargetResult:
    ladder: EvidenceLadderResult
    feature_amplitude_bootstrap_ci: tuple[float, float]
    segment_preferences: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    target: TargetResult | None = None
    warnings: list[str] = field(default_factory=list)


def _feature_amplitude_bootstrap(spectrum: WASP39bSpectrum, seed: int = 20260713) -> tuple[float, float]:
    """Bootstrap CI on the mean (data - no_feature_model) within the CO
    band (defined as the wavelength range where the real published
    CO-only model component exceeds 10% of its own peak)."""
    peak = np.max(np.abs(spectrum.model_feature_only))
    if peak <= 0.0:
        raise InsufficientDataError("_feature_amplitude_bootstrap: feature-only model has zero peak amplitude")
    threshold = 0.1 * peak
    band_mask = np.abs(spectrum.model_feature_only) >= threshold
    if band_mask.sum() < 2:
        raise InsufficientDataError("_feature_amplitude_bootstrap: fewer than 2 points in the CO band")
    residual_in_band = (spectrum.transit_depth - spectrum.model_no_feature)[band_mask]
    result = bootstrap_statistic(residual_in_band, statistic=np.mean, seed=seed)
    return (result.ci_low, result.ci_high)


def run_pipeline(manifest_rows: list[dict[str, str]], raw_dir: Path, config: AnalysisConfig) -> PipelineResult:
    """Run the evidence-ladder pipeline over the real WASP-39b spectrum
    listed in the manifest.

    Raises `InsufficientDataError` immediately if the manifest is empty.
    Per-step failures (segment too small, bootstrap failure) are caught and
    converted to warnings rather than aborting the whole run.
    """
    if not manifest_rows:
        raise InsufficientDataError("run_pipeline: manifest_rows is empty")

    warnings: list[str] = []
    product_id = manifest_rows[0].get("product_id", "UNKNOWN")
    nc_path = Path(raw_dir) / f"{product_id}.nc"

    try:
        spectrum = load_spectrum(nc_path)
    except DataSchemaError as exc:
        return PipelineResult(target=None, warnings=[f"{product_id}: skipped (load failure): {exc}"])

    ladder = evidence_ladder(
        data=spectrum.transit_depth, uncertainty=spectrum.transit_depth_err,
        model_simple=spectrum.model_no_feature, model_complex=spectrum.model_full,
        n_params_simple=N_PARAMS_SIMPLE, n_params_complex=N_PARAMS_COMPLEX,
    )

    try:
        amplitude_ci = _feature_amplitude_bootstrap(spectrum)
    except InsufficientDataError as exc:
        warnings.append(f"{product_id}: feature-amplitude bootstrap skipped: {exc}")
        amplitude_ci = (float("nan"), float("nan"))

    segment_edges = np.linspace(spectrum.wavelength_um.min(), spectrum.wavelength_um.max(), N_SEGMENTS + 1)
    segment_preferences: list[str] = []
    for i in range(N_SEGMENTS):
        seg_mask = (spectrum.wavelength_um >= segment_edges[i]) & (spectrum.wavelength_um <= segment_edges[i + 1])
        if seg_mask.sum() < 3:
            warnings.append(f"{product_id}: segment {i} has fewer than 3 points, skipped in leave-one-out")
            continue
        try:
            seg_ladder = evidence_ladder(
                data=spectrum.transit_depth[seg_mask], uncertainty=spectrum.transit_depth_err[seg_mask],
                model_simple=spectrum.model_no_feature[seg_mask], model_complex=spectrum.model_full[seg_mask],
                n_params_simple=N_PARAMS_SIMPLE, n_params_complex=N_PARAMS_COMPLEX,
            )
            segment_preferences.append(seg_ladder.preferred_model)
        except (InsufficientDataError, ConvergenceError, DataSchemaError) as exc:
            warnings.append(f"{product_id}: segment {i} evidence ladder skipped: {exc}")

    target = TargetResult(ladder=ladder, feature_amplitude_bootstrap_ci=amplitude_ci, segment_preferences=segment_preferences)
    return PipelineResult(target=target, warnings=warnings)
