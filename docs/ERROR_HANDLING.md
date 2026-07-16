# Error Handling Contract

Raise actionable exceptions for missing files, unsupported schemas, checksum failures, invalid units, inconsistent array lengths, empty selections, non-finite values, underpopulated bins and failed numerical convergence.

Warnings must be collected in `results/warnings.json`. Never silently drop invalid products or replace missing values with zero unless the method explicitly justifies it.
