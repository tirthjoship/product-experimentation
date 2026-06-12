"""Loader tests — scenarios (verdict verbatim), motivation, DiD list shape."""

from pathlib import Path

import pytest

from dashboard.data import (
    ReportSchemaError,
    load_did,
    load_motivation,
    load_scenarios,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_scenarios_rejects_non_list_root(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"scenario": "large"}')  # object, not the expected list
    with pytest.raises(ReportSchemaError, match="list of scenarios"):
        load_scenarios(bad)


def test_load_did_rejects_empty_list_root(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[]")  # empty list — no event to read
    with pytest.raises(ReportSchemaError, match="non-empty list"):
        load_did(bad)


def test_load_scenarios_reads_verdicts_verbatim() -> None:
    scenarios = load_scenarios(FIXTURES / "scenarios.json")
    assert [s.scenario for s in scenarios] == ["adverse", "null", "large"]
    assert [s.verdict for s in scenarios] == ["DO NOT SHIP", "NEED MORE DATA", "SHIP"]
    null = scenarios[1]
    assert null.result.aov.lift == pytest.approx(2.06)
    assert null.result.aov_adjusted.lift == pytest.approx(0.54)


def test_load_motivation_preserves_bucket_order() -> None:
    stats = load_motivation(FIXTURES / "motivation.json")
    assert [b.bucket for b in stats.buckets] == ["1", "2-3", "4-6", "7+"]
    assert stats.buckets[-1].aov == pytest.approx(337.03)
    assert 0.0 <= stats.share_multi_installment <= 1.0
    assert 0.0 <= stats.credit_card_value_share <= 1.0
    assert stats.n_orders == 1000


def test_load_did_handles_list_shape_and_string_lead_keys() -> None:
    did = load_did(FIXTURES / "did.json")
    assert did.event == "truckers_strike_2018"
    assert did.verdict == "FAIL"
    assert did.dated_boundary_passed is True
    assert did.boundary_date == "2018-05-21"
    assert did.exogenous_passed is True
    assert did.pretrends.passed is False
    assert did.pretrends.wald_p == pytest.approx(0.018)
    assert did.pretrends.band == pytest.approx(1.93)
    assert sorted(did.pretrends.leads) == [-5, -4, -3, -2]
    assert did.pretrends.leads[-2] == pytest.approx(3.4)
    assert did.adequate_n.passed is False
    assert did.adequate_n.treated_orders == 3604
    assert did.adequate_n.week_cell_share_ge_20 == pytest.approx(0.45)
