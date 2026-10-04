"""Load the public WASP-39 b products released with Grant et al. (2023)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from jwst_wasp39b_evidence_ladder.exceptions import DataSchemaError

REQUIRED_VARIABLES = (
    "wavelength_native_resolution",
    "transit_depth_native_resolution",
    "transit_depth_err_native_resolution",
    "model_native_resolution",
    "model_no_co_native_resolution",
    "model_only_co_native_resolution",
)


@dataclass(frozen=True)
class WASP39bSpectrum:
    wavelength_um: np.ndarray
    transit_depth: np.ndarray
    transit_depth_err: np.ndarray
    model_full: np.ndarray
    model_no_feature: np.ndarray
    model_feature_only: np.ndarray


@dataclass(frozen=True)
class COSubBandSamples:
    """Observed transit depths selected by the authors' CO sub-band mask."""

    wavelength_in_um: np.ndarray
    depth_in: np.ndarray
    wavelength_out_um: np.ndarray
    depth_out: np.ndarray


SUB_BAND_VARIABLES = (
    "wavelength_in_co_sub_bands",
    "transit_depths_in_co_sub_bands",
    "wavelength_out_of_co_sub_bands",
    "transit_depths_out_of_co_sub_bands",
)


def load_spectrum(path: str | Path) -> WASP39bSpectrum:
    """Load the real Grant et al. (2023) WASP-39b netCDF product.

    Raises `DataSchemaError` for a missing file or missing/malformed
    required variables.
    """
    nc_path = Path(path)
    if not nc_path.is_file():
        raise DataSchemaError(f"spectrum file not found: {nc_path}")

    try:
        import netCDF4
    except ImportError as exc:  # pragma: no cover - environment guard
        raise DataSchemaError("netCDF4 is not installed in this environment") from exc

    try:
        with netCDF4.Dataset(nc_path, "r") as ds:
            available = set(ds.variables.keys())
            missing = [v for v in REQUIRED_VARIABLES if v not in available]
            if missing:
                raise DataSchemaError(f"{nc_path}: missing required variables: {missing}")

            wavelength = np.asarray(ds.variables["wavelength_native_resolution"][:], dtype=float)
            depth = np.asarray(ds.variables["transit_depth_native_resolution"][:], dtype=float)
            depth_err = np.asarray(ds.variables["transit_depth_err_native_resolution"][:], dtype=float)
            model_full = np.asarray(ds.variables["model_native_resolution"][:], dtype=float)
            model_no_feature = np.asarray(ds.variables["model_no_co_native_resolution"][:], dtype=float)
            model_feature_only = np.asarray(ds.variables["model_only_co_native_resolution"][:], dtype=float)
    except OSError as exc:
        raise DataSchemaError(f"{nc_path}: could not be opened as netCDF: {exc}") from exc

    if wavelength.size == 0:
        raise DataSchemaError(f"{nc_path}: spectrum has zero wavelength points")

    order = np.argsort(wavelength)
    return WASP39bSpectrum(
        wavelength_um=wavelength[order], transit_depth=depth[order], transit_depth_err=depth_err[order],
        model_full=model_full[order], model_no_feature=model_no_feature[order],
        model_feature_only=model_feature_only[order],
    )


def load_co_sub_band_samples(path: str | Path) -> COSubBandSamples:
    """Load the exact in/out samples used for the paper's Welch test."""
    nc_path = Path(path)
    if not nc_path.is_file():
        raise DataSchemaError(f"CO sub-band file not found: {nc_path}")
    try:
        import netCDF4
    except ImportError as exc:  # pragma: no cover
        raise DataSchemaError("netCDF4 is not installed in this environment") from exc

    try:
        with netCDF4.Dataset(nc_path, "r") as ds:
            missing = [name for name in SUB_BAND_VARIABLES if name not in ds.variables]
            if missing:
                raise DataSchemaError(f"{nc_path}: missing required variables: {missing}")
            wi = np.asarray(ds.variables[SUB_BAND_VARIABLES[0]][:], dtype=float)
            di = np.asarray(ds.variables[SUB_BAND_VARIABLES[1]][:], dtype=float)
            wo = np.asarray(ds.variables[SUB_BAND_VARIABLES[2]][:], dtype=float)
            do = np.asarray(ds.variables[SUB_BAND_VARIABLES[3]][:], dtype=float)
    except OSError as exc:
        raise DataSchemaError(f"{nc_path}: could not be opened as netCDF: {exc}") from exc

    if wi.size < 2 or wo.size < 2 or wi.size != di.size or wo.size != do.size:
        raise DataSchemaError(f"{nc_path}: invalid CO sub-band array lengths")
    if not all(np.all(np.isfinite(x)) for x in (wi, di, wo, do)):
        raise DataSchemaError(f"{nc_path}: CO sub-band arrays contain non-finite values")
    oi, oo = np.argsort(wi), np.argsort(wo)
    return COSubBandSamples(wi[oi], di[oi], wo[oo], do[oo])
