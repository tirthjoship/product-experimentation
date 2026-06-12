"""TWFE DiD: must recover a known injected effect; CI must cover 0 under null;
estimate invariant to state-constant shifts (hypothesis property)."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.did.estimator import fit_twfe
from tests.did_factory import make_synthetic_panel


def test_recovers_injected_effect():
    panel = make_synthetic_panel(effect=5.0, seed=42)
    res = fit_twfe(panel, "delivery_days")
    assert res.beta == pytest.approx(5.0, abs=0.5)
    assert res.ci[0] < 5.0 < res.ci[1]
    assert res.n_clusters == 16


def test_null_effect_ci_covers_zero():
    panel = make_synthetic_panel(effect=0.0, seed=42)
    res = fit_twfe(panel, "delivery_days")
    assert res.ci[0] < 0.0 < res.ci[1]


@settings(max_examples=20, deadline=None)
@given(shift=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False))
def test_beta_invariant_to_global_shift(shift):
    panel = make_synthetic_panel(effect=3.0, seed=42)
    res_base = fit_twfe(panel, "delivery_days")
    shifted = panel.copy()
    shifted["delivery_days"] = shifted["delivery_days"] + shift
    res_shift = fit_twfe(shifted, "delivery_days")
    assert res_shift.beta == pytest.approx(res_base.beta, abs=1e-8)


def test_fit_twfe_tolerates_nan_outcome_cells():
    """Real data has state×week cells with no delivered orders -> NaN outcome.
    statsmodels drops those rows; groups must align or cov_cluster raises."""
    import numpy as np

    panel = make_synthetic_panel(effect=4.0, seed=7)
    panel.loc[panel.index[:5], "delivery_days"] = np.nan  # punch holes
    res = fit_twfe(panel, "delivery_days")  # must not raise
    assert res.beta == res.beta  # not NaN
