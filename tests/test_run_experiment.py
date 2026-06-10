from src.experiment.run_experiment import run
from src.report.experiment_report import generate_report


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
