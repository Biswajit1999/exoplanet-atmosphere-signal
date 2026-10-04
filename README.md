# Carbon monoxide in WASP-39 b

A transparent computational reproduction of the JWST/NIRSpec G395H CO sub-band experiment reported by Grant et al. (2023). The repository ships the complete three-file Zenodo record, verifies every product by SHA-256, reproduces the paper's released-array contrast, and adds deterministic sensitivity analyses.

## Result

The 111 released in-band samples have a mean transit depth **263.66 ± 67.68 ppm** greater than the 145 released out-of-band samples (Welch unequal-variance t = 3.895; one-sided p = 6.30 × 10⁻⁵). A 10,000-resample within-group bootstrap gives a 95% interval of **130.38–394.03 ppm**.

This matches the article's quoted 264 ± 68 ppm result. It is a reproduction from the authors' derived products, not a new detector-level reduction or an independent blind molecular search.

## Robustness and diagnostics

- The 4.4–4.7 µm and 4.7–5.0 µm zones both retain positive contrasts: 363.27 and 196.46 ppm.
- Deleting each contiguous selected wavelength run in turn gives an estimate range of 244.7–280.3 ppm.
- An exploratory 20,000-draw label permutation gives p = 1.00 × 10⁻⁴, subject to its exchangeability assumption.
- The archived full curve improves χ² by 75.65 relative to the archived no-CO curve, but both are fixed products rather than models refit by this repository. No AIC, BIC, Bayes factor, abundance posterior, or detection significance is inferred from that difference.

The deposited sub-band file contains 111 in-band and 145 out-of-band values; the article text reports 111 and 148. The pipeline uses the archived arrays unchanged and records this discrepancy in every result bundle.

## Reproduce

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# POSIX: source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q
python scripts/run_analysis.py
python scripts/make_figures.py
python scripts/sync_web_assets.py
```

The inputs are already committed under `data/raw/`. To refetch the upstream record deliberately:

```bash
python scripts/fetch_data.py --i-have-authorization
```

## Scientific scope

Primary estimand: the mean transit-depth difference between the authors' model-selected CO in-bands and comparison bands. Primary test: a one-sided Welch unequal-variance t-test in the physical direction specified by the paper. The bootstrap, permutation, wavelength-zone, and contiguous-run analyses are robustness checks; they do not change the estimand.

Neighbouring spectral pixels may be correlated, band selection is model-informed, and the workflow starts from released derived spectra. These boundaries are described in `data/provenance.yml` and surfaced in the web report.

## Data and citation

- Grant et al. (2023), *Detection of Carbon Monoxide's 4.6 micron Fundamental Band Structure in WASP-39b's Atmosphere with JWST NIRSpec G395H*, ApJL 956 L32, [doi:10.3847/2041-8213/acfc3b](https://doi.org/10.3847/2041-8213/acfc3b)
- Released products: [Zenodo 10.5281/zenodo.7866690](https://doi.org/10.5281/zenodo.7866690)
- File-level provenance and checksums: `data/manifest.csv`

Original repository code is licensed under the repository `LICENSE`. Archived research products retain the terms stated by their source record.
