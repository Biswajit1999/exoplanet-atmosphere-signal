"""Generate the required figures: spectrum overlays, residuals, evidence
ladder, bootstrap amplitudes, segment stability. --demo uses synthetic data;
default uses the real WASP-39b spectrum.
"""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401 - importing registers the SciencePlots styles

from jwst_wasp39b_evidence_ladder import __version__ as PACKAGE_VERSION
from jwst_wasp39b_evidence_ladder.config import load_config
from jwst_wasp39b_evidence_ladder.core import N_PARAMS_COMPLEX, N_PARAMS_SIMPLE, N_SEGMENTS, _feature_amplitude_bootstrap
from jwst_wasp39b_evidence_ladder.io import WASP39bSpectrum, load_spectrum
from jwst_wasp39b_evidence_ladder.metrics import evidence_ladder
from jwst_wasp39b_evidence_ladder.provenance import get_git_commit, read_manifest, sha256_config
from jwst_wasp39b_evidence_ladder.synthetic import SyntheticSpectrumSpec, make_synthetic_spectrum

plt.style.use(["science", "no-latex"])

REPO_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = REPO_ROOT / "figures"


def _sidecar(name: str, data_kind: str, sample_size: int, units: str, config_path: Path) -> dict:
    return {
        "figure": name,
        "data_kind": data_kind,
        "sample_size": sample_size,
        "units": units,
        "git_commit": get_git_commit(REPO_ROOT),
        "config_sha256": sha256_config(config_path),
        "package_version": PACKAGE_VERSION,
        "python_version": platform.python_version(),
    }


def _save(fig, name: str, data_kind: str, sample_size: int, units: str, config_path: Path) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{name}.svg", dpi=180)
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=300)
    plt.close(fig)
    sidecar = _sidecar(name, data_kind, sample_size, units, config_path)
    (FIGURES_DIR / f"{name}.json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")


def _spectrum_from_synthetic(inject_feature: bool) -> WASP39bSpectrum:
    spec = SyntheticSpectrumSpec()
    syn = make_synthetic_spectrum(spec, seed=20260713, inject_feature=inject_feature)
    flat = syn.transit_depth * 0.0 + spec.baseline
    feature_only = syn.transit_depth - flat if inject_feature else flat * 0.0
    return WASP39bSpectrum(
        wavelength_um=syn.wavelength_um, transit_depth=syn.transit_depth, transit_depth_err=syn.transit_depth_err,
        model_full=syn.transit_depth, model_no_feature=flat, model_feature_only=feature_only,
    )


def _make_all_figures(spectrum: WASP39bSpectrum, data_kind: str, config_path: Path) -> None:
    n = spectrum.wavelength_um.size

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(spectrum.wavelength_um, spectrum.transit_depth, yerr=spectrum.transit_depth_err,
                fmt="o", ms=3, color="black", ecolor="gray", alpha=0.6, label="observed")
    ax.plot(spectrum.wavelength_um, spectrum.model_no_feature, color="tab:blue", label="no-CO model")
    ax.plot(spectrum.wavelength_um, spectrum.model_full, color="tab:red", label="full model (with CO)")
    ax.set_xlabel("Wavelength (um)")
    ax.set_ylabel("Transit depth (Rp/Rs)^2")
    ax.set_title("WASP-39b transmission spectrum: model overlays")
    ax.legend()
    _save(fig, "fig01_spectrum_overlays", data_kind, n, "transit depth (Rp/Rs)^2", config_path)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axhline(0.0, color="gray", linestyle="--")
    ax.errorbar(spectrum.wavelength_um, spectrum.transit_depth - spectrum.model_no_feature,
                yerr=spectrum.transit_depth_err, fmt="o", ms=3, color="tab:blue", label="data - no-CO model")
    ax.plot(spectrum.wavelength_um, spectrum.model_feature_only, color="tab:red", label="CO-only model component")
    ax.set_xlabel("Wavelength (um)")
    ax.set_ylabel("Residual transit depth")
    ax.set_title("Residuals against the no-CO model")
    ax.legend()
    _save(fig, "fig02_residuals", data_kind, n, "transit depth (Rp/Rs)^2", config_path)

    ladder = evidence_ladder(
        data=spectrum.transit_depth, uncertainty=spectrum.transit_depth_err,
        model_simple=spectrum.model_no_feature, model_complex=spectrum.model_full,
        n_params_simple=N_PARAMS_SIMPLE, n_params_complex=N_PARAMS_COMPLEX,
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    labels = ["AIC", "BIC"]
    simple_vals = [ladder.aic_simple, ladder.bic_simple]
    complex_vals = [ladder.aic_complex, ladder.bic_complex]
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width / 2, simple_vals, width, label="no-CO model", color="tab:blue")
    ax.bar(x + width / 2, complex_vals, width, label="full model", color="tab:red")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Information criterion value (lower is preferred)")
    ax.set_title(f"Evidence ladder: preferred = {ladder.preferred_model}")
    ax.legend()
    _save(fig, "fig03_evidence_ladder", data_kind, n, "AIC/BIC units", config_path)

    try:
        ci_lo, ci_hi = _feature_amplitude_bootstrap(spectrum)
        estimate = (ci_lo + ci_hi) / 2.0
    except Exception:
        ci_lo, ci_hi, estimate = float("nan"), float("nan"), float("nan")
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.errorbar([0], [estimate], yerr=[[estimate - ci_lo], [ci_hi - estimate]], fmt="o", ms=8, color="tab:red")
    ax.axhline(0.0, color="gray", linestyle="--", label="zero (no feature)")
    ax.set_xticks([])
    ax.set_ylabel("Mean residual amplitude in CO band")
    ax.set_title("Bootstrap CI: feature amplitude (95%)")
    ax.legend()
    _save(fig, "fig04_bootstrap_amplitudes", data_kind, n, "transit depth (Rp/Rs)^2", config_path)

    segment_edges = np.linspace(spectrum.wavelength_um.min(), spectrum.wavelength_um.max(), N_SEGMENTS + 1)
    seg_labels, seg_delta_aic = [], []
    for i in range(N_SEGMENTS):
        mask = (spectrum.wavelength_um >= segment_edges[i]) & (spectrum.wavelength_um <= segment_edges[i + 1])
        if mask.sum() < 3:
            continue
        seg_ladder = evidence_ladder(
            data=spectrum.transit_depth[mask], uncertainty=spectrum.transit_depth_err[mask],
            model_simple=spectrum.model_no_feature[mask], model_complex=spectrum.model_full[mask],
            n_params_simple=N_PARAMS_SIMPLE, n_params_complex=N_PARAMS_COMPLEX,
        )
        seg_labels.append(f"seg{i} ({segment_edges[i]:.2f}-{segment_edges[i+1]:.2f}um)")
        seg_delta_aic.append(seg_ladder.delta_aic)
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["tab:red" if v > 0 else "tab:blue" for v in seg_delta_aic]
    ax.bar(seg_labels, seg_delta_aic, color=colors)
    ax.axhline(0.0, color="gray", linestyle="--")
    ax.set_ylabel("Delta AIC (positive favours full model)")
    ax.set_title("Leave-one-segment-out sensitivity")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _save(fig, "fig05_segment_stability", data_kind, n, "AIC units", config_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        spectrum = _spectrum_from_synthetic(inject_feature=True)
        _make_all_figures(spectrum, "synthetic_demo", args.config)
        print(f"Demo figures written to {FIGURES_DIR}")
    else:
        config = load_config(args.config)
        manifest_rows = read_manifest(config.input.manifest)
        if not manifest_rows:
            raise SystemExit(
                f"No manifest rows found at {config.input.manifest}. "
                "Run scripts/fetch_data.py --i-have-authorization first."
            )
        product_id = manifest_rows[0]["product_id"]
        nc_path = Path(config.input.raw_directory) / f"{product_id}.nc"
        spectrum = load_spectrum(nc_path)
        _make_all_figures(spectrum, "real WASP-39b JWST NIRSpec spectrum", args.config)
        print(f"Real-data figures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
