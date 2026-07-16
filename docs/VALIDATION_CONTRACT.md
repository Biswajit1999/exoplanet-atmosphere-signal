# Validation Contract

## Required checks

- weighted chi-square
- AIC/BIC ladder
- bootstrap feature amplitudes
- leave-one-segment-out test

## Minimum acceptance rules

1. All scientific arrays are finite after documented masking.
2. Units and coordinate conventions are explicit.
3. Synthetic/injection recovery has a known truth value.
4. Uncertainty is reported through bootstrap, propagation, convergence, or an equivalent justified method.
5. At least one null, negative-control or failure-mode test is included.
6. Results can be regenerated from a clean clone using scripts, not notebook-only state.
7. Benchmarks record hardware, Python version, dataset size and command.

## Reporting

Write machine-readable results to `results/summary.json` and warnings to `results/warnings.json`.
