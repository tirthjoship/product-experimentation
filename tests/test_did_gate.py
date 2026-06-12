"""Gate: 4 pre-registered conditions; verdict JSON unlocks (or keeps locked) post-period."""

import json

import pandas as pd

from src.did.catalog import get_event
from src.did.gate import evaluate_gate, feasibility_counts, write_verdict
from tests.did_factory import make_synthetic_panel

EVENT = get_event("truckers_strike_2018")


def _pre(panel: pd.DataFrame) -> pd.DataFrame:
    return panel[~panel["post"]].reset_index(drop=True)


def test_feasibility_counts_structure():
    pre = _pre(make_synthetic_panel(seed=42))
    fc = feasibility_counts(pre)
    assert fc["treated_orders"] > 0 and fc["control_orders"] > 0
    assert 0.0 <= fc["week_cell_share_ge_20"] <= 1.0
    assert fc["treated_states"] == 8 and fc["control_states"] == 8


def test_gate_go_on_clean_panel():
    pre = _pre(make_synthetic_panel(effect=0.0, pre_trend=0.0, seed=42))
    verdict = evaluate_gate(EVENT, pre)
    assert verdict["verdict"] == "GO"
    assert all(c["passed"] for c in verdict["conditions"].values()), verdict[
        "conditions"
    ]


def test_gate_fail_on_diverging_pretrend():
    pre = _pre(make_synthetic_panel(effect=0.0, pre_trend=1.0, seed=42))
    verdict = evaluate_gate(EVENT, pre)
    assert verdict["verdict"] == "FAIL"
    assert not verdict["conditions"]["parallel_pretrends"]["passed"]


def test_gate_fail_on_thin_cells():
    pre = _pre(make_synthetic_panel(seed=42))
    thin = pre.copy()
    thin["n_orders"] = 1  # every cell below thresholds
    verdict = evaluate_gate(EVENT, thin)
    assert verdict["verdict"] == "FAIL"
    assert not verdict["conditions"]["adequate_n"]["passed"]


def test_write_verdict_roundtrip(tmp_path):
    pre = _pre(make_synthetic_panel(seed=42))
    verdict = evaluate_gate(EVENT, pre)
    path = tmp_path / "verdict.json"
    write_verdict(verdict, path)
    assert json.loads(path.read_text())["event"] == "truckers_strike_2018"
    assert "computed_at" not in verdict  # determinism: git is the timestamp
