# Research Blueprint

## Technical title

JWST WASP-39 b Transmission-Spectrum Evidence Ladder

## Category

Exoplanet atmosphere data science

## Bounded scientific question

How stable are simple nested-model feature preferences in public WASP-39 b transmission spectra under bootstrap and instrument-segment sensitivity?

## Gap statement

A transparent model-comparison bridge; not a full atmospheric retrieval or replacement for TauREx/petitRADTRANS.

## First-release scope

The first release must be completable as a focused 4–6 hour implementation pass after data access is working. It must deliver one reproducible analysis pipeline, one deterministic example/smoke dataset, tests, 4–6 figures, a concise TeX report and a deployable research webpage.

## Validation and uncertainty

- weighted chi-square
- AIC/BIC ladder
- bootstrap feature amplitudes
- leave-one-segment-out test

## Required figures

1. spectrum overlays
2. residuals
3. evidence ladder
4. bootstrap amplitudes
5. segment stability

## Reusable scientific modules

- `io.py`
- `models.py`
- `fitting.py`
- `metrics.py`
- `uncertainty.py`
- `plotting.py`

## Explicit exclusions

- No novelty claim beyond the bounded dataset/question/method combination.
- No causal claim from descriptive catalogue correlations.
- No hidden manual data editing.
- No unsupported precision beyond the input uncertainties.
- No production-pipeline replacement claim.
