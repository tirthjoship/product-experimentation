import json

import pytest

from src.experiment.run_experiment import run, write_outputs
from src.report.experiment_report import generate_report
from src.report.results_io import results_to_json


def test_run_returns_expected_shape(base_con):
    results = run(base_con)
    assert set(results) >= {
        "sample_sizes",
        "aov",
        "conversion",
        "d7",
        "mde",
        "simulated_effect",
    }
    assert results["sample_sizes"]["control"] == 3
    assert results["sample_sizes"]["treatment"] == 3
    assert results["simulated_effect"] == 0.05


def test_run_feeds_report(base_con):
    md = generate_report(run(base_con))
    assert "Recommendation" in md
    assert "simulated" in md.lower()


def test_write_outputs_emits_md_and_json(base_con, tmp_path):
    results = run(base_con)
    report_path = tmp_path / "experiment_001.md"
    json_path = tmp_path / "experiment_001.json"
    write_outputs(results, report_path, json_path)
    assert report_path.exists()
    parsed = json.loads(json_path.read_text())
    # ci tuple serialized as a 2-element list
    assert len(parsed["aov"]["ci"]) == 2
    assert "simulated_effect" in parsed


def test_run_is_deterministic_for_p3_contract(base_con):
    # Same connection, two runs -> byte-identical JSON. Codifies the P3 regression contract.
    first = results_to_json(run(base_con))
    second = results_to_json(run(base_con))
    assert first == second


def test_run_accepts_effect_override(base_con):
    # The tiny fixture has treatment group with lower raw mean than control, so we
    # cannot assert treatment > control on raw AOV.  Instead we assert that a
    # larger injected effect produces a meaningfully higher treatment AOV, and that
    # the returned simulated_effect reflects the kwarg.
    null = run(base_con, effect=0.0)
    big = run(base_con, effect=0.20)
    # Bigger effect must lift treatment AOV relative to no-effect baseline.
    null_treat = null["aov"]["treatment"]
    big_treat = big["aov"]["treatment"]
    assert isinstance(null_treat, float)
    assert isinstance(big_treat, float)
    assert big_treat == pytest.approx(null_treat * 1.20, rel=1e-6)
    # simulated_effect key must reflect the kwarg, not the module constant.
    assert null["simulated_effect"] == pytest.approx(0.0)
    assert big["simulated_effect"] == pytest.approx(0.20)


def test_write_scenarios_emits_md_and_json(base_con, tmp_path):
    from src.experiment.run_experiment import write_scenarios_outputs
    from src.experiment.scenarios import run_scenarios

    scenarios = run_scenarios(base_con)
    md_path = tmp_path / "experiment_scenarios.md"
    json_path = tmp_path / "experiment_scenarios.json"
    write_scenarios_outputs(scenarios, md_path, json_path)
    assert md_path.exists()
    import json

    parsed = json.loads(json_path.read_text())
    assert len(parsed) == len(scenarios)
    assert parsed[0]["scenario"] == scenarios[0]["scenario"]
