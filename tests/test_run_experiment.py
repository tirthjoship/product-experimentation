import json

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
