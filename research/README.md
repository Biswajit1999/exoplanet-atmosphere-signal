# Conditional spectral-template robustness (2026-11-04)

Scope tracked in [issue #1](https://github.com/Biswajit1999/exoplanet-atmosphere-signal/issues/1). This is a **standalone synthetic diagnostic**, not a WASP-39 b CO abundance inference. It does not change the existing observational pipeline, archival provenance or published figures.

Three analyses: (1) Cholesky-whitened generalized least squares for a linear template design with known full covariance, reporting absolute parameter covariance and reduced chi-square; (2) stationary AR(1) covariance sensitivity for equally spaced wavelength bins; and (3) seeded parametric injection recovery with empirical bias, dispersion and nominal 95% interval coverage. The covariance model is illustrative, not estimated from JWST instrument residuals.

Reproduce: `PYTHONPATH=research python -m pytest -q research/test_robustness.py` (numpy and pytest). Inputs must be finite and covariance positive definite; ill-conditioned template designs may fail, appropriately. Future integration requires measured covariance, wavelength-aware treatment and observational provenance updates. No scientific figures were regenerated because no existing figures or observational outputs were changed.
