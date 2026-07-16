from __future__ import annotations

import pytest

from jwst_wasp39b_evidence_ladder.synthetic import SyntheticSpectrumSpec, make_synthetic_spectrum


@pytest.fixture
def synthetic_spec() -> SyntheticSpectrumSpec:
    return SyntheticSpectrumSpec()


@pytest.fixture
def synthetic_spectrum_with_feature(synthetic_spec):
    return make_synthetic_spectrum(synthetic_spec, seed=20260713, inject_feature=True)


@pytest.fixture
def synthetic_spectrum_null(synthetic_spec):
    return make_synthetic_spectrum(synthetic_spec, seed=20260713, inject_feature=False)
