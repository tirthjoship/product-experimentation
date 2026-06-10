from src.report.experiment_report import generate_report

RESULTS = {
    "sample_sizes": {"control": 49575, "treatment": 49866},
    "aov": {
        "control": 160.0,
        "treatment": 168.0,
        "lift": 8.0,
        "ci": (3.0, 13.0),
        "p": 0.001,
    },
    "conversion": {
        "control": 0.97,
        "treatment": 0.971,
        "z": 0.5,
        "p": 0.61,
        "ci": (-0.002, 0.004),
    },
    "d7": {"control": 0.002, "treatment": 0.0022},
    "mde": {"aov": 3.95, "conversion": 0.003},
    "simulated_effect": 0.05,
}


def test_disclaimer_present():
    md = generate_report(RESULTS)
    assert "simulated" in md.lower()
    assert "SIMULATED_EFFECT" in md or "0.05" in md


def test_ship_when_ci_positive():
    md = generate_report(RESULTS)
    assert "SHIP" in md


def test_do_not_ship_when_ci_negative():
    r = dict(RESULTS)
    r["aov"] = {**RESULTS["aov"], "lift": -8.0, "ci": (-13.0, -3.0)}
    assert "DO NOT SHIP" in generate_report(r)


def test_need_more_data_when_ci_spans_zero():
    r = dict(RESULTS)
    r["aov"] = {**RESULTS["aov"], "lift": 1.0, "ci": (-2.0, 4.0)}
    assert "NEED MORE DATA" in generate_report(r)


def test_sample_sizes_rendered():
    md = generate_report(RESULTS)
    assert "49575" in md and "49866" in md
