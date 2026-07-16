import numpy as np
import pytest

from jwst_wasp39b_evidence_ladder.core import demo_series, robust_summary, validate_numeric


def test_demo_is_deterministic() -> None:
    assert np.array_equal(demo_series(), demo_series())


def test_summary_is_finite() -> None:
    summary = robust_summary(demo_series())
    assert summary.count == 128
    assert np.isfinite(summary.median)
    assert summary.mad > 0


def test_invalid_values_rejected() -> None:
    with pytest.raises(ValueError):
        validate_numeric(np.array([1.0, np.nan]))
