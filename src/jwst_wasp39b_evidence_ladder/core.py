"""Pipeline orchestration for the released WASP-39 b CO sub-band experiment."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from jwst_wasp39b_evidence_ladder.config import AnalysisConfig
from jwst_wasp39b_evidence_ladder.exceptions import DataSchemaError, InsufficientDataError
from jwst_wasp39b_evidence_ladder.io import (
    COSubBandSamples,
    load_co_sub_band_samples,
    load_spectrum,
)
from jwst_wasp39b_evidence_ladder.metrics import (
    FixedCurveDiagnostic,
    WelchContrast,
    fixed_curve_diagnostic,
    welch_sub_band_contrast,
)


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


@dataclass
class TargetResult:
    contrast: WelchContrast
    bootstrap_ci_ppm: tuple[float, float]
    permutation_p_one_sided: float
    fixed_curves: FixedCurveDiagnostic
    zone_contrasts_ppm: dict[str, float] = field(default_factory=dict)
    leave_one_run_range_ppm: tuple[float, float] = (float("nan"), float("nan"))


@dataclass
class PipelineResult:
    target: TargetResult | None = None
    warnings: list[str] = field(default_factory=list)


def bootstrap_contrast(
    samples: COSubBandSamples, n_resamples: int = 10_000, seed: int = 20260713,
) -> tuple[float, float]:
    """Percentile interval from independent resampling within the two bands."""
    rng = np.random.default_rng(seed)
    inside, outside = samples.depth_in * 1e6, samples.depth_out * 1e6
    draws = np.empty(n_resamples)
    for index in range(n_resamples):
        draws[index] = (
            rng.choice(inside, inside.size, replace=True).mean()
            - rng.choice(outside, outside.size, replace=True).mean()
        )
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def permutation_p_value(
    samples: COSubBandSamples, n_permutations: int = 20_000, seed: int = 20260713,
) -> float:
    """Exploratory one-sided randomisation check under exchangeable labels."""
    rng = np.random.default_rng(seed)
    inside, outside = samples.depth_in * 1e6, samples.depth_out * 1e6
    observed = inside.mean() - outside.mean()
    pooled = np.concatenate((inside, outside))
    exceedances = 0
    for _ in range(n_permutations):
        shuffled = rng.permutation(pooled)
        exceedances += int(shuffled[: inside.size].mean() - shuffled[inside.size :].mean() >= observed)
    return (exceedances + 1) / (n_permutations + 1)


def _leave_one_run_range(samples: COSubBandSamples) -> tuple[float, float]:
    """Delete contiguous wavelength runs to expose local spectral leverage."""
    all_wavelengths = np.sort(np.concatenate((samples.wavelength_in_um, samples.wavelength_out_um)))
    native_spacing = float(np.median(np.diff(all_wavelengths)))

    def runs(wavelength: np.ndarray) -> list[np.ndarray]:
        return list(np.split(np.arange(wavelength.size), np.where(np.diff(wavelength) > 3 * native_spacing)[0] + 1))

    values: list[float] = []
    for group, other, wavelength in (
        (samples.depth_in, samples.depth_out, samples.wavelength_in_um),
        (samples.depth_out, samples.depth_in, samples.wavelength_out_um),
    ):
        for run in runs(wavelength):
            retained = np.delete(group, run)
            if group is samples.depth_in:
                values.append(float((retained.mean() - other.mean()) * 1e6))
            else:
                values.append(float((other.mean() - retained.mean()) * 1e6))
    return min(values), max(values)


def run_pipeline(manifest_rows: list[dict[str, str]], raw_dir: Path, config: AnalysisConfig) -> PipelineResult:
    """Reproduce the paper's estimand and add transparent robustness checks."""
    if not manifest_rows:
        raise InsufficientDataError("run_pipeline: manifest_rows is empty")

    warnings: list[str] = []
    try:
        spectrum_id = next(row["product_id"] for row in manifest_rows if "transmission_spectrum" in row["product_id"])
        bands_id = next(row["product_id"] for row in manifest_rows if "co_sub_band" in row["product_id"])
        spectrum = load_spectrum(Path(raw_dir) / f"{spectrum_id}.nc")
        samples = load_co_sub_band_samples(Path(raw_dir) / f"{bands_id}.nc")
    except DataSchemaError as exc:
        return PipelineResult(target=None, warnings=[f"load failure: {exc}"])
    except StopIteration:
        return PipelineResult(target=None, warnings=["manifest must include spectrum and CO sub-band products"])

    contrast = welch_sub_band_contrast(samples.depth_in, samples.depth_out)
    fixed = fixed_curve_diagnostic(
        spectrum.transit_depth, spectrum.transit_depth_err,
        spectrum.model_no_feature, spectrum.model_full,
    )
    zones: dict[str, float] = {}
    for low, high in ((4.4, 4.7), (4.7, 5.01)):
        in_mask = (samples.wavelength_in_um >= low) & (samples.wavelength_in_um < high)
        out_mask = (samples.wavelength_out_um >= low) & (samples.wavelength_out_um < high)
        if in_mask.sum() >= 2 and out_mask.sum() >= 2:
            zones[f"{low:.1f}-{min(high, 5.0):.1f} um"] = float(
                (samples.depth_in[in_mask].mean() - samples.depth_out[out_mask].mean()) * 1e6
            )

    if contrast.n_out != 148:
        warnings.append(
            f"Zenodo sub-band file contains {contrast.n_out} out-of-band samples; "
            "the paper text reports 148. Calculations use the archived arrays without alteration."
        )
    warnings.append(
        "Fixed-curve chi-square values are descriptive only: neither atmospheric model was refit here, "
        "so AIC, BIC, Bayes factors, and abundance constraints are not identified by this workflow."
    )
    target = TargetResult(
        contrast=contrast,
        bootstrap_ci_ppm=bootstrap_contrast(samples, config.validation.bootstrap_resamples, config.execution.seed),
        permutation_p_one_sided=permutation_p_value(samples, seed=config.execution.seed),
        fixed_curves=fixed,
        zone_contrasts_ppm=zones,
        leave_one_run_range_ppm=_leave_one_run_range(samples),
    )
    return PipelineResult(target=target, warnings=warnings)
