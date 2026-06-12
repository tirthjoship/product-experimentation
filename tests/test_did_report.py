"""Report writers: every number in md comes from the dict that also writes the JSON
(house rule 1). Simulation banner not needed — this analysis is observational."""

from src.did.catalog import get_event
from src.did.estimator import DidResult
from src.did.gate import evaluate_gate
from src.did.report import (
    generate_did_report_md,
    generate_feasibility_md,
    generate_rejection_md,
)
from tests.did_factory import make_synthetic_panel

EVENT = get_event("truckers_strike_2018")


def _verdict(pre_trend: float = 0.0):
    panel = make_synthetic_panel(pre_trend=pre_trend, seed=42)
    return evaluate_gate(EVENT, panel[~panel["post"]].reset_index(drop=True))


def test_feasibility_md_contains_counts():
    v = _verdict()
    md = generate_feasibility_md([v])
    n = v["conditions"]["adequate_n"]
    assert f"{n['treated_orders']:,}" in md
    assert f"{n['control_orders']:,}" in md
    assert "truckers_strike_2018" in md
    assert "outcome-blind" in md.lower()


def test_go_report_quotes_estimate_and_gate():
    v = _verdict()
    res = DidResult(
        beta=2.5,
        se=0.4,
        ci=(1.7, 3.3),
        p=0.001,
        n_obs=288,
        n_clusters=16,
        outcome="delivery_days",
    )
    md = generate_did_report_md(EVENT, res, v)
    assert "2.50" in md and "(1.70, 3.30)" in md
    assert "natural experiment" in md.lower()
    assert "threats to validity" in md.lower()


def test_rejection_md_names_broken_condition():
    v = _verdict(pre_trend=1.0)
    md = generate_rejection_md(EVENT, v)
    assert "REJECTED" in md
    assert "parallel_pretrends" in md
