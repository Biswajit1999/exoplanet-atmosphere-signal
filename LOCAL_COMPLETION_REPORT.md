# Local Completion Report — JWST WASP-39 b Transmission-Spectrum Evidence Ladder

Author: Biswajit Jana. This report documents a local Claude Code implementation pass
(project 11 of the 30-project pack, `BUILD_FIRST` priority 8.8/10). No git operations
were performed. Nothing has been published. This is the last project in the
30-project pack's `BUILD_FIRST` queue. The repository folder is named
`exoplanet-atmosphere-signal` (a simpler, human-readable name; the original pack
folder/package name was `jwst-wasp39b-evidence-ladder`, retained internally as the
Python distribution/import name under `src/jwst_wasp39b_evidence_ladder/`).

## 1. Environment

- Ran against the machine's base Python 3.9 (Anaconda) environment with the
  project's `src/` layer on `PYTHONPATH` (no dedicated conda env was created
  this session; `pyproject.toml` still declares `requires-python = ">=3.11,<3.13"`
  and the pinned dependency set — a genuine mismatch worth reconciling, see
  Section 7).
- Added `netCDF4==1.6.5` as a new pinned dependency, justified by the real
  Zenodo data file format (documented in `IMPLEMENTATION_PLAN.md`).
- No local LaTeX toolchain.

## 2. Files created or changed

This project's entire `src/` layer, tests, and scripts were built from a raw
stub scaffold this session: foundation (`config.py`, `exceptions.py`,
`logging_utils.py`, `provenance.py`, `results_io.py`), data layer (`io.py`
for the real netCDF spectrum loader, `scripts/fetch_data.py`), scientific
modules (`models.py`, `fitting.py`, `metrics.py`, `uncertainty.py`,
`synthetic.py`, `core.py`), 6 test files (32 tests), figures/report
(`scripts/make_figures.py`, `reports/report.tex`, `reports/references.bib`),
`scripts/sync_web_assets.py`, and the web dashboard (`web-react/src/App.jsx`
rewritten from the established template, `eslint.config.js` fixed,
`recharts` removed, `public/project.json` rewritten).

## 3. Exact commands run (in order)

```bash
PYTHONPATH=src python -m pytest -q                 # 32 passed (after 2 fixes, see below)
python -m ruff check .                              # All checks passed (after 2 fixes)
python -m mypy src                                  # Success: no issues found in 14 source files
PYTHONPATH=src python scripts/fetch_data.py --i-have-authorization
PYTHONPATH=src python scripts/run_analysis.py
PYTHONPATH=src python scripts/make_figures.py
PYTHONPATH=src python scripts/sync_web_assets.py
cd web-react && npm install && npm run lint && npm run build
```

## 4. Test / lint / build results

- **pytest**: 32 tests passed, 0 failed.
- **ruff**: clean on the full project.
- **mypy**: clean on `src` (0 errors, 14 source files).
- **web-react**: `npm run lint` and `npm run build` both clean.

### Bugs found and fixed during implementation

1. **Real edge-case bug in `core._feature_amplitude_bootstrap`**: the CO-band
   mask used `abs(model_feature_only) >= 0.1 * peak`; when the feature-only
   model is degenerately all-zero (peak = 0), the comparison `0 >= 0` is
   true everywhere, silently including every point in the "CO band" instead
   of correctly signalling that there is no usable band. Fixed by explicitly
   raising `InsufficientDataError` when the feature-only model's peak
   amplitude is exactly zero, caught by a targeted unit test.
2. **Expected-but-uncaught `ConvergenceError` in the null-control test**:
   fitting an unconstrained 4-parameter Gaussian to pure noise (no injected
   feature) is genuinely expected to produce an ill-conditioned covariance
   matrix, since there is no real feature for the fit to lock onto. The
   initial null-control test assumed the fit would always converge; fixed by
   treating `ConvergenceError` on the null-control path as itself a valid
   null-control outcome (the pipeline must not silently report a confident,
   ill-conditioned fit as evidence for the complex model), not by loosening
   the convergence threshold.
3. Two minor ruff lint fixes (unused import, unused local variable) in test
   files.

## 5. Real datasets accessed

- **File**: `2_transmission_spectra_and_models.nc` (60,320 bytes), from
  Zenodo record 10.5281/zenodo.7866690 (Grant, Lothringer, Wakeford et al.
  2023, arXiv:2304.11994), live-verified via the Zenodo API and by
  inspecting the file's own internal `doi` attribute before this pipeline
  was written.
- **Substitution documented transparently**: the originally-scoped
  "benchmark JWST spectrum" Zenodo record (10161743,
  `ERS_DataSynthesis_Zenodo.zip`, 1.74\,GB) was rejected as too large for a
  bounded first release; the much smaller, directly relevant, real
  CO-detection paper's data (record 7866690) was used instead.
- **Licence/terms**: Zenodo open-access deposit; standard Zenodo/CC licence
  terms per the deposit page.
- Full SHA-256 (`61c05c57...`) and provenance in `data/manifest.csv`. The
  raw netCDF file is not committed.

## 6. Validation and uncertainty outcomes

- **Synthetic injection-recovery gate**: PASSED. A known injected Gaussian
  feature (amplitude 1.5e-3, center 4.6 um, width 0.08 um) is recovered by
  `fit_flat_plus_gaussian` to within 5e-4 of truth, and the evidence ladder
  correctly prefers the complex model.
- **Null control**: PASSED. On matched synthetic data with no injected
  feature, the evidence ladder does not prefer the complex model (and in
  some realizations the unconstrained Gaussian fit itself fails to
  converge, itself part of the null-control signal — see bug #2 above).
- **Real-data result, the central finding**: over the real full spectrum
  (1008 points, 3.82-5.16 um), the evidence ladder strongly prefers the
  full (CO) model over the no-CO model: chi2_no-CO=1230.09,
  chi2_full=1154.44, Delta-AIC=73.65, Delta-BIC=68.74 — both far above the
  conventional "strong evidence" threshold (>6), consistent with the real
  paper's own CO detection. The bootstrap 95% CI on the mean residual
  amplitude in the CO band, [1.35e-4, 2.52e-4], excludes zero. In the
  leave-one-segment-out check, 2 of 3 wavelength segments individually
  prefer the CO model; the one that does not (the low-wavelength third,
  ~3.82-4.27 um, mostly blueward of the CO band) is consistent with the
  known physical location of the CO feature (~4.3-4.6 um), not a
  contradiction of the full-spectrum result.

## 7. Remaining TODOs / unresolved risks

- `reports/report.tex` could not be compiled to PDF locally (no LaTeX
  toolchain); structural completeness and real-number substitution were
  checked, not a rendered PDF.
- This session ran against the base Python 3.9 environment rather than a
  dedicated `>=3.11` conda env matching `pyproject.toml`'s declared
  `requires-python`; all tests/lint/mypy/pipeline runs succeeded on 3.9 in
  practice, but a dedicated 3.11 env should be created before any future
  work, per the pattern used in sibling projects.
- Only one real target (a single reduced-visit spectrum) is available from
  the Zenodo product actually used; no multi-target real-data comparison
  in this first release.
- The no-CO -> full-model "1 effective parameter" framing is a documented
  simplification, not the real atmospheric retrieval's exact
  free-parameter count (see `IMPLEMENTATION_PLAN.md` and `report.tex`
  Limitations).

## 8. Claims safe for a public README

- "A transparent model-comparison bridge over a real, published WASP-39b
  JWST NIRSpec transmission spectrum (Grant et al. 2023), reproducing the
  paper's own CO detection via an independent weighted chi-square/AIC/BIC
  evidence ladder, bootstrap confidence interval, and wavelength-segment
  sensitivity check."
- "32 automated tests including a synthetic injection-recovery validation
  gate and a null control (including a genuine fit-convergence edge case);
  ruff- and mypy-clean."
- "Not a full atmospheric retrieval and not a replacement for
  TauREx/petitRADTRANS — a transparent, independently reproducible
  verification of the published model comparison."

## 9. Claims that must NOT be made

- Do not claim this project performs its own atmospheric retrieval or
  spectral fitting of the real spectrum — the real full/no-CO models used
  are the paper's own published models, not independently derived here.
- Do not claim the "1 effective parameter" AIC/BIC penalty matches the real
  retrieval's true parameter count.
- Do not claim the TeX report PDF has been visually verified — only its
  source structure and real-number substitution were checked.
- Do not claim multi-target or multi-visit real-data coverage — only one
  real reduced spectrum was analysed.

## 10. Manual review checklist for Biswajit

- [ ] Compile `reports/report.tex` locally/Overleaf and read the PDF end-to-end.
- [ ] Create a dedicated Python 3.11 conda env matching `pyproject.toml`
      before any future work on this project.
- [ ] Review `npm audit` output and decide whether to bump pinned frontend
      tooling.
- [ ] Follow the manual GitHub repo creation process for this and all 10
      other completed projects, using the new repo name
      `exoplanet-atmosphere-signal` — none of that was done in this session.
