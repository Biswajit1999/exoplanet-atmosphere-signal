# Wavelength-bin influence and block-deletion diagnostics

Scientific scope issue: https://github.com/Biswajit1999/exoplanet-atmosphere-signal/issues/5

Run from this directory with `python -m unittest discover -s . -p 'test_*.py'`. Dependencies: NumPy. The methods compute (1) weighted leverage and exact leave-one-bin-out coefficient changes, and (2) refit changes when removing fixed-width wavelength blocks. The wavelength block origin is the smallest input wavelength; these are sensitivity diagnostics, not independent statistical trials.

Formal covariance assumes a fixed full-rank linear design and independent Gaussian errors with known marginal sigma. No empirical inter-bin covariance is inferred. Failed deletion fits return NaNs; interpret these as identifiability failures. This does not reprocess telescope observations or establish molecular detections. Existing GLS and AR(1) draft PRs remain separate.

A reproducible synthetic figure can be generated with `python plot_synthetic.py` (Matplotlib required); no observed spectrum is represented. AI-assisted implementation and testing; Biswajit Jana is the requested sole Git author. Review numerical and scientific assumptions before merging.
