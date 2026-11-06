# Conditional spectral covariance research (2026-11-05)

Addresses [issue #1](https://github.com/Biswajit1999/exoplanet-atmosphere-signal/issues/1).
Three diagnostics: (1) Cholesky-whitened generalized least-squares template amplitude and formal uncertainty; (2) AR(1) spectral-correlation sensitivity; (3) seeded Gaussian injection-recovery interval coverage. Reproduce from repository root with `python -m unittest discover -s tests -p 'test_spectral_covariance_audit.py'` after installing NumPy.

**Physics and provenance:** The template, covariance, amplitudes and Gaussian draws are *synthetic*; this is not a fit to the JWST WASP-39 b data, not a detection, and not a calibrated instrument-noise model. C is treated as known, fixed and positive definite. The Gaussian confidence interval has nominal 68.27% coverage only under this model. AR(1) rho is hypothetical; no measured spectral covariance is claimed. No original observational products are changed. Scientific implementation prepared with AI assistance and submitted through the authenticated Biswajit Jana GitHub identity. Independent review is required before merging.
