"""Two-sided pre-trends gate input: Wald on leads catches divergence; the magnitude
band exists so vacuous non-significance can't pass silently (spec §6 condition 3)."""

import pytest

from src.did.estimator import pretrends_check
from tests.did_factory import make_synthetic_panel


def test_parallel_panel_passes_wald():
    panel = make_synthetic_panel(effect=5.0, pre_trend=0.0, seed=42)
    pt = pretrends_check(panel, "delivery_days", "2018-05-21")
    assert pt.wald_p > 0.10
    assert pt.n_leads >= 3
    assert pt.max_lead_abs <= pt.band


def test_diverging_pretrend_fails_wald():
    panel = make_synthetic_panel(effect=5.0, pre_trend=1.0, seed=42)
    pt = pretrends_check(panel, "delivery_days", "2018-05-21")
    assert pt.wald_p <= 0.10 or pt.max_lead_abs > pt.band


def test_pretrends_uses_pre_period_only():
    # identical pre-periods, wildly different post-periods -> identical results
    a = make_synthetic_panel(effect=0.0, seed=42)
    b = make_synthetic_panel(effect=50.0, seed=42)
    pt_a = pretrends_check(a, "delivery_days", "2018-05-21")
    pt_b = pretrends_check(b, "delivery_days", "2018-05-21")
    assert pt_a.wald_p == pytest.approx(pt_b.wald_p)
    assert pt_a.leads == pt_b.leads
