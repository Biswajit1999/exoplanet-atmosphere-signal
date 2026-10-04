"""Generate publication-style figures from the archived Grant et al. products."""
from __future__ import annotations

import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from jwst_wasp39b_evidence_ladder import __version__ as PACKAGE_VERSION
from jwst_wasp39b_evidence_ladder.config import load_config
from jwst_wasp39b_evidence_ladder.core import run_pipeline
from jwst_wasp39b_evidence_ladder.io import load_co_sub_band_samples, load_spectrum
from jwst_wasp39b_evidence_ladder.provenance import get_git_commit, read_manifest, sha256_config

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"font.size": 9, "axes.titlesize": 11, "axes.labelsize": 9})

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
INK, BLUE, RED, GOLD = "#17202a", "#246a8d", "#aa3a2f", "#ad7a14"


def save(fig, name: str, caption: str, n: int, config_path: Path) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)
    sidecar = {
        "figure": name, "caption": caption, "data_kind": "archived JWST/NIRSpec G395H products",
        "sample_size": n, "git_commit": get_git_commit(ROOT),
        "config_sha256": sha256_config(config_path), "package_version": PACKAGE_VERSION,
        "python_version": platform.python_version(),
    }
    (FIGURES / f"{name}.json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")


def main() -> None:
    config_path = Path("config/analysis.yml")
    config = load_config(config_path)
    rows = read_manifest(config.input.manifest)
    result = run_pipeline(rows, Path(config.input.raw_directory), config)
    if result.target is None:
        raise SystemExit("Analysis products unavailable: " + "; ".join(result.warnings))
    target = result.target
    spectrum = load_spectrum(Path(config.input.raw_directory) / "wasp39b_grant2023_transmission_spectrum.nc")
    samples = load_co_sub_band_samples(Path(config.input.raw_directory) / "wasp39b_grant2023_co_sub_band_samples.nc")

    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    ax.errorbar(spectrum.wavelength_um, spectrum.transit_depth * 1e6,
                yerr=spectrum.transit_depth_err * 1e6, fmt=".", ms=2.2, alpha=.35,
                color=INK, ecolor="#9aa2aa", label="observed native-resolution spectrum")
    ax.plot(spectrum.wavelength_um, spectrum.model_no_feature * 1e6, color=BLUE, lw=1.2, label="archived no-CO curve")
    ax.plot(spectrum.wavelength_um, spectrum.model_full * 1e6, color=RED, lw=1.2, label="archived full curve")
    ax.set(xlabel="Wavelength (µm)", ylabel="Transit depth (ppm)", title="Released WASP-39 b spectrum and fixed model curves")
    ax.legend(frameon=False, ncol=3, fontsize=7, loc="upper left")
    save(fig, "fig01_spectrum", "Native-resolution spectrum with the two archived, non-refit curves.", spectrum.wavelength_um.size, config_path)

    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.scatter(samples.wavelength_out_um, samples.depth_out * 1e6, s=13, color=BLUE, alpha=.72, label=f"out of CO bands (n={samples.depth_out.size})")
    ax.scatter(samples.wavelength_in_um, samples.depth_in * 1e6, s=16, color=RED, alpha=.82, label=f"in CO bands (n={samples.depth_in.size})")
    ax.axhline(target.contrast.mean_out_ppm, color=BLUE, lw=1, ls="--")
    ax.axhline(target.contrast.mean_in_ppm, color=RED, lw=1, ls="--")
    ax.set(xlabel="Wavelength (µm)", ylabel="Transit depth (ppm)", title="Author-selected samples used by the CO sub-band test")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "fig02_sub_band_samples", "Exact released in/out samples; dashed lines mark group means.", 256, config_path)

    c = target.contrast
    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    ax.errorbar([0], [c.contrast_ppm], yerr=[[c.contrast_ppm-c.ci95_low_ppm], [c.ci95_high_ppm-c.contrast_ppm]], fmt="o", ms=8, color=RED, capsize=5, label="Welch 95% CI")
    ax.errorbar([1], [c.contrast_ppm], yerr=[[c.contrast_ppm-target.bootstrap_ci_ppm[0]], [target.bootstrap_ci_ppm[1]-c.contrast_ppm]], fmt="s", ms=7, color=BLUE, capsize=5, label="bootstrap 95% interval")
    ax.axhline(0, color=INK, lw=.8)
    ax.set_xticks([0, 1], ["Welch", "bootstrap"])
    ax.set(ylabel="In-band − out-of-band depth (ppm)", title=f"CO sub-band contrast: {c.contrast_ppm:.0f} ± {c.standard_error_ppm:.0f} ppm")
    ax.text(.98, .06, f"t = {c.t_statistic:.2f}\none-sided p = {c.p_one_sided:.2g}", transform=ax.transAxes, ha="right", va="bottom", fontsize=8)
    ax.legend(frameon=False, fontsize=8)
    save(fig, "fig03_contrast", "Primary contrast with parametric and nonparametric uncertainty.", 256, config_path)

    labels = ["overall", *target.zone_contrasts_ppm.keys()]
    values = [c.contrast_ppm, *target.zone_contrasts_ppm.values()]
    fig, ax = plt.subplots(figsize=(6.8, 4.3))
    ax.barh(labels, values, color=[RED, GOLD, GOLD], alpha=.88)
    ax.axvline(0, color=INK, lw=.8)
    ax.axvspan(*target.leave_one_run_range_ppm, color=BLUE, alpha=.16, label="leave-one-run range")
    ax.set(xlabel="In-band − out-of-band depth (ppm)", title="Sensitivity across wavelength and local spectral runs")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "fig04_sensitivity", "Broad-zone contrasts and leave-one-contiguous-run influence range.", 256, config_path)

    residual_no = (spectrum.transit_depth - spectrum.model_no_feature) / spectrum.transit_depth_err
    residual_full = (spectrum.transit_depth - spectrum.model_full) / spectrum.transit_depth_err
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 5.2), sharex=True, sharey=True)
    axes[0].scatter(spectrum.wavelength_um, residual_no, s=5, color=BLUE, alpha=.5)
    axes[1].scatter(spectrum.wavelength_um, residual_full, s=5, color=RED, alpha=.5)
    for ax, label, chi in zip(axes, ("no-CO archived curve", "full archived curve"), (target.fixed_curves.chi2_per_point_no_co, target.fixed_curves.chi2_per_point_full)):
        ax.axhline(0, color=INK, lw=.7); ax.set_ylabel("Residual / σ"); ax.text(.01, .88, f"{label}; χ²/N={chi:.3f}", transform=ax.transAxes, fontsize=8)
    axes[1].set_xlabel("Wavelength (µm)")
    axes[0].set_title("Fixed-curve residual diagnostic (descriptive; models not refit)")
    save(fig, "fig05_fixed_curve_residuals", "Standardised residuals for archived fixed curves; not an information-criterion comparison.", 1008, config_path)
    print(f"Wrote five scientific figures to {FIGURES}")


if __name__ == "__main__":
    main()
