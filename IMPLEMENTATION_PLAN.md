# Implementation Plan — JWST WASP-39 b Transmission-Spectrum Evidence Ladder

Author: Biswajit Jana. Local Claude Code implementation pass, project from the
30-project portfolio pack (`BUILD_FIRST`, priority 8.8/10). No git operations.

## 1. Literature verification (done before any code)

| Seed citation | Verification method | Result |
|---|---|---|
| Grant, Lothringer, Wakeford et al. 2023, "Detection of carbon monoxide's 4.6 micron fundamental band structure in WASP-39b's atmosphere with JWST NIRSpec G395H", arXiv:2304.11994 | WebFetch arXiv abstract page | VERIFIED — real title/authors/subject match. |
| Zenodo data deposit for the above paper, DOI 10.5281/zenodo.7866690 | Zenodo API (`zenodo.org/api/records/7866690`) | VERIFIED — files listed match ("1_light_curves.nc", "2_transmission_spectra_and_models.nc", "3_co_sub_band_samples.nc"); DOI cross-referenced inside the netCDF file's own `doi` attribute (`https://doi.org/10.48550/arXiv.2304.11994`), confirming the file and the paper are the same source. |
| Alderson et al. 2022/2023, WASP-39b NIRSpec G395H ERS paper, arXiv:2211.10488 | WebFetch arXiv abstract page | VERIFIED — real title/authors, but this is a DIFFERENT paper (the initial full-transit ERS characterization) from the CO-detection paper actually used for data (above); cited for context only, not as the data source. |
| TauREx III, petitRADTRANS framework papers | Not independently re-verified this session (secondary tooling references, not load-bearing for the method implemented here, which is a custom weighted chi-square/AIC/BIC ladder, not TauREx/petitRADTRANS) — marked `TODO_VERIFY` if cited in report.tex. |

## 2. Real-data access plan (verified live against Zenodo)

- Real reduced transmission-spectrum data comes from Zenodo record
  10.5281/zenodo.7866690 (Grant et al. 2023), file
  `2_transmission_spectra_and_models.nc` (60.3 KB, small enough to commit-safe
  download without violating the "no large raw files" rule).
- **Live-verified file contents** (netCDF3, opened directly): real observed
  transit depth + uncertainty at native and 30-pixel resolution
  (`transit_depth_native_resolution`, `transit_depth_err_native_resolution`,
  `wavelength_native_resolution`), plus the paper's own **real published
  best-fit models**: `model_native_resolution` (full model including CO),
  `model_no_co_native_resolution` (nested model with CO removed), and
  `model_only_co_native_resolution` (CO-only component). This is a genuine,
  directly-usable real "evidence ladder" pair (full vs. nested/no-feature
  model) from a real peer-reviewed paper, not a self-generated model.
- `data/manifest.csv` records the Zenodo product_id/source_url/retrieved_utc/
  sha256/file_size_bytes/selection_reason/licence_or_terms; raw file is
  small enough to be committed if desired but is treated as `data/raw/`
  (gitignored) for consistency with sibling projects.
- Real "instrument segments" for the leave-one-segment-out validation item:
  the native-resolution wavelength grid is split into contiguous wavelength
  segments (e.g. thirds of the G395H bandpass) as a practical proxy for
  "instrument segment" since this is a single-grating (G395H) dataset, not a
  multi-instrument spectrum — documented as a scope simplification.

## 3. File-level task list

### Foundation (ported near-verbatim from sibling projects, package renamed)
- `config.py`, `exceptions.py` (extend), `logging_utils.py`, `provenance.py`
  (extend), `results_io.py` (new).

### Data layer
- `synthetic.py` (new) — synthetic spectrum generator with a known injected
  absorption feature (known depth/width/wavelength) plus a matched flat/no-feature
  model, for the required injection-recovery validation gate.
- `scripts/fetch_data.py` — real Zenodo fetch, gated behind
  `--i-have-authorization`, checksums, manifest row.

### Scientific modules (docs/RESEARCH_BLUEPRINT.md)
- `io.py` — load the real netCDF spectrum+models file (via `netCDF4`, a new
  pinned dependency justified by the real file format); raise
  `DataSchemaError` on missing variables.
- `models.py` — simple parametric spectrum models (flat continuum; flat +
  single Gaussian absorption feature) used for the synthetic validation gate,
  plus direct pass-through of the real paper's own full/no-CO models for the
  real-data nested comparison.
- `fitting.py` — weighted least-squares fit of `models.py` model parameters
  to a spectrum (`scipy.optimize.curve_fit`) for the synthetic gate; for real
  data, the real paper's models are used as-is (no re-fitting invented).
- `metrics.py` — weighted chi-square, AIC, BIC computation given a model,
  data, uncertainties and parameter count; nested-model preference decision
  (favour the model with lower AIC/BIC, by how much).
- `uncertainty.py` — `bootstrap_statistic` (1000 resamples, seed 20260713)
  and `check_fit_convergence` (covariance condition number + reduced
  chi-square), kept strictly separate.
- `plotting.py` — figure-building helpers used by `scripts/make_figures.py`.
- `core.py` — `run_pipeline` orchestrator: real-data evidence ladder (full
  vs. no-CO model chi-square/AIC/BIC), bootstrap feature-amplitude stability,
  leave-one-wavelength-segment-out sensitivity; per-configuration
  try/except over `InsufficientDataError`/`ConvergenceError`/`DataSchemaError`
  -> warning, never abort.

### Validation/QA
- `tests/conftest.py` — synthetic fixtures.
- Injection-recovery gate: known injected Gaussian absorption feature
  correctly preferred (lower AIC/BIC) over the flat-continuum model when
  present; correctly NOT preferred (flat continuum wins) when absent (null
  control) -- both directions required.
- Failure-mode tests: missing netCDF variables, empty spectrum, non-finite
  input.
- Benchmarks via `tracemalloc` + `time.perf_counter()`.

### Figures + report
- `scripts/make_figures.py` — 5 required figures (spectrum overlays;
  residuals; evidence ladder; bootstrap amplitudes; segment stability),
  SVG+PNG(300dpi)+sidecar JSON.
- `reports/report.tex` + `reports/references.bib` — real numbers only after
  real pipeline run.

### React dashboard
- `web-react/eslint.config.js` — add `react/jsx-uses-vars`/`react/jsx-uses-react`.
- `web-react/package.json` — remove `recharts`.
- `web-react/src/App.jsx` — replace stub using established template.
- `web-react/public/project.json` — rewrite with real fields, repo name
  `exoplanet-atmosphere-signal`.
- `scripts/sync_web_assets.py` (new) — copy results/figures/manifest into
  `web-react/public/`.

### Final
- `LOCAL_COMPLETION_REPORT.md`, `_PROJECT_LOG.md` — filled in after real-data
  run.

## 4. Environment

Dedicated conda env `exoplanet-atmosphere-signal`, Python 3.11. This
project's pyproject.toml adds `netCDF4==1.6.5` beyond the standard pinned
set, justified by the real Zenodo data file format (netCDF3/HDF5-based);
documented explicitly rather than silently added.

## 5. Stop conditions encountered

None yet identified as hard blockers. The originally-scoped 1.74\,GB Zenodo
"benchmark spectrum" deposit (record 10161743) was rejected as too large for
a bounded first release; the much smaller (60.3\,KB), directly relevant
CO-detection paper's data (record 7866690) was used instead — a real,
verified substitution, not a fabricated shortcut.
