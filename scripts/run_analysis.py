"""Run the evidence-ladder analysis: --demo (synthetic smoke test/injection
gate) or real-data path (real WASP-39b spectrum via manifest + core.run_pipeline).

Peak memory is measured with the stdlib `tracemalloc` (Python-level
allocations) rather than a full process-RSS profiler such as psutil, which
is not part of this project's pinned dependency set.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import tracemalloc
from pathlib import Path

from jwst_wasp39b_evidence_ladder import __version__ as PACKAGE_VERSION
from jwst_wasp39b_evidence_ladder.config import load_config
from jwst_wasp39b_evidence_ladder.core import N_PARAMS_COMPLEX, N_PARAMS_SIMPLE, run_pipeline
from jwst_wasp39b_evidence_ladder.exceptions import InsufficientDataError
from jwst_wasp39b_evidence_ladder.logging_utils import get_logger
from jwst_wasp39b_evidence_ladder.metrics import evidence_ladder
from jwst_wasp39b_evidence_ladder.provenance import get_git_commit, read_manifest, sha256_config
from jwst_wasp39b_evidence_ladder.results_io import Metric, write_summary
from jwst_wasp39b_evidence_ladder.synthetic import SyntheticSpectrumSpec, make_synthetic_spectrum

LOGGER = get_logger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[1]


def _provenance(config_path: Path) -> dict:
    return {
        "git_commit": get_git_commit(REPO_ROOT),
        "config_sha256": sha256_config(config_path),
        "package_version": PACKAGE_VERSION,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def _write_benchmark(path: Path, label: str, wall_time_s: float, peak_memory_mib: float, dataset_size: int) -> None:
    payload = {
        "label": label,
        "wall_time_seconds": wall_time_s,
        "peak_memory_mib": peak_memory_mib,
        "peak_memory_method": "tracemalloc (Python-level allocations, not full process RSS)",
        "dataset_size": dataset_size,
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "package_version": PACKAGE_VERSION,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    existing.append(payload)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def run_demo(config_path: Path, out_path: Path) -> None:
    tracemalloc.start()
    start = time.perf_counter()

    spec = SyntheticSpectrumSpec()
    injected = make_synthetic_spectrum(spec, seed=20260713, inject_feature=True)
    null = make_synthetic_spectrum(spec, seed=20260713, inject_feature=False)
    flat_injected = injected.transit_depth * 0.0 + spec.baseline
    flat_null = null.transit_depth * 0.0 + spec.baseline

    ladder_injected = evidence_ladder(
        data=injected.transit_depth, uncertainty=injected.transit_depth_err,
        model_simple=flat_injected, model_complex=injected.transit_depth,
        n_params_simple=N_PARAMS_SIMPLE, n_params_complex=N_PARAMS_COMPLEX,
    )
    ladder_null = evidence_ladder(
        data=null.transit_depth, uncertainty=null.transit_depth_err,
        model_simple=flat_null, model_complex=flat_null,
        n_params_simple=N_PARAMS_SIMPLE, n_params_complex=N_PARAMS_COMPLEX,
    )

    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics = [
        Metric(name="synthetic_injected_delta_aic", estimate=ladder_injected.delta_aic, units="AIC units", sample_size=spec.n_points),
        Metric(name="synthetic_null_delta_aic", estimate=ladder_null.delta_aic, units="AIC units", sample_size=spec.n_points),
    ]
    warnings = ["synthetic demo run: not derived from real archive data"]
    write_summary(
        out_path, project="exoplanet-atmosphere-signal", data_kind="synthetic_demo",
        metrics=metrics, provenance=_provenance(config_path),
        warnings=warnings,
    )
    (out_path.parent / "warnings.json").write_text(json.dumps(warnings, indent=2), encoding="utf-8")
    _write_benchmark(out_path.parent / "benchmarks.json", "demo", elapsed, peak / (1024 * 1024), spec.n_points)
    print(f"Demo summary written to {out_path}")


def run_real(config_path: Path) -> None:
    config = load_config(config_path)
    manifest_rows = read_manifest(config.input.manifest)
    if not manifest_rows:
        raise SystemExit(
            f"No manifest rows found at {config.input.manifest}. "
            "Run scripts/fetch_data.py --i-have-authorization first."
        )

    tracemalloc.start()
    start = time.perf_counter()

    try:
        result = run_pipeline(manifest_rows, Path(config.input.raw_directory), config)
    except InsufficientDataError as exc:
        raise SystemExit(f"Pipeline could not run: {exc}") from exc

    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics: list[Metric] = []
    warnings = list(result.warnings)
    if result.target is not None:
        ladder = result.target.ladder
        ci_lo, ci_hi = result.target.feature_amplitude_bootstrap_ci
        estimate = (ci_lo + ci_hi) / 2.0 if ci_lo == ci_lo else float("nan")
        metrics.extend([
            Metric(name="chi2_no_feature_model", estimate=ladder.chi2_simple, units="chi-square", sample_size=len(manifest_rows)),
            Metric(name="chi2_full_model", estimate=ladder.chi2_complex, units="chi-square", sample_size=len(manifest_rows)),
            Metric(name="delta_aic", estimate=ladder.delta_aic, units="AIC units", sample_size=len(manifest_rows)),
            Metric(name="delta_bic", estimate=ladder.delta_bic, units="BIC units", sample_size=len(manifest_rows)),
            Metric(
                name="feature_amplitude_mean_residual_in_co_band",
                estimate=estimate, units="transit depth (Rp/Rs)^2", sample_size=len(manifest_rows),
                uncertainty_low=ci_lo, uncertainty_high=ci_hi,
            ),
        ])
        n_complex_preferred = sum(1 for p in result.target.segment_preferences if p == "complex")
        warnings.append(
            f"preferred_model (full spectrum): {ladder.preferred_model}; "
            f"segment preferences: {result.target.segment_preferences} "
            f"({n_complex_preferred}/{len(result.target.segment_preferences)} segments favour the CO model)"
        )
    else:
        warnings.append("no target result produced; see warnings above for load failure detail")

    results_dir = Path(config.execution.output_directory)
    out_path = results_dir / "summary.json"
    write_summary(
        out_path, project="exoplanet-atmosphere-signal", data_kind="real WASP-39b JWST NIRSpec spectrum",
        metrics=metrics, provenance=_provenance(config_path), warnings=warnings,
    )
    (results_dir / "warnings.json").write_text(json.dumps(warnings, indent=2), encoding="utf-8")
    _write_benchmark(results_dir / "benchmarks.json", "real_data", elapsed, peak / (1024 * 1024), len(manifest_rows))
    print(f"Real-data summary written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--demo", action="store_true", help="Run the fast synthetic smoke test instead of real data")
    parser.add_argument("--out", type=Path, default=Path("results/summary.json"))
    args = parser.parse_args()

    if args.demo:
        run_demo(args.config, args.out)
    else:
        run_real(args.config)


if __name__ == "__main__":
    main()
