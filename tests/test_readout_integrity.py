"""Enforce rule 1 (no invented metrics) on the PM memo: every headline number quoted in
reports/experiment_001_readout.md must match the committed JSON artifacts, using the
same format strings the memo uses."""

import json
from pathlib import Path

MEMO_PATH = Path("reports/experiment_001_readout.md")
EXPERIMENT_JSON = Path("reports/experiment_001.json")
SCENARIOS_JSON = Path("reports/experiment_scenarios.json")
MOTIVATION_JSON = Path("reports/installment_motivation.json")


def _memo() -> str:
    return MEMO_PATH.read_text()


def test_headline_numbers_match_experiment_json():
    e = json.loads(EXPERIMENT_JSON.read_text())
    adj = e["aov_adjusted"]
    memo = _memo()
    assert f"{adj['lift']:.2f}" in memo
    assert f"({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f})" in memo
    assert f"{e['aov']['lift']:.2f}" in memo
    assert f"({e['aov']['ci'][0]:.2f}, {e['aov']['ci'][1]:.2f})" in memo
    assert f"{adj['ci_width_ratio']:.0%}" in memo
    assert f"{e['sample_sizes']['control']:,}" in memo
    assert f"{e['sample_sizes']['treatment']:,}" in memo
    assert f"{e['mde']['aov']:.2f}" in memo


def test_guardrail_numbers_match_experiment_json():
    e = json.loads(EXPERIMENT_JSON.read_text())
    memo = _memo()
    assert f"{e['conversion']['control']:.4f}" in memo
    assert f"{e['conversion']['treatment']:.4f}" in memo


def test_scenario_numbers_and_verdicts_match_scenarios_json():
    scenarios = {s["scenario"]: s for s in json.loads(SCENARIOS_JSON.read_text())}
    memo = _memo()
    null = scenarios["null"]
    assert f"{null['aov']['lift']:.2f}" in memo
    assert f"{null['aov_adjusted']['lift']:.2f}" in memo
    for s in scenarios.values():
        assert str(s["verdict"]) in memo


def test_motivation_numbers_match_motivation_json():
    m = json.loads(MOTIVATION_JSON.read_text())
    memo = _memo()
    assert f"{m['share_multi_installment_orders']:.1%}" in memo
    assert f"{m['credit_card_value_share']:.1%}" in memo


def test_simulation_disclaimer_prominent():
    memo = _memo()
    assert "simulated" in memo[:600].lower()  # top
    assert memo.lower().count("simulated") >= 2  # top and bottom
