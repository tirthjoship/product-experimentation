from src.report.experiment_report import generate_report, generate_scenarios_report

AOV_ADJUSTED = {
    "control": 100.0,
    "treatment": 103.0,
    "lift": 3.0,
    "ci": (1.0, 5.0),
    "theta": 0.8,
    "ci_width_ratio": 0.7,
}

RESULTS = {
    "sample_sizes": {"control": 49575, "treatment": 49866},
    "aov": {
        "control": 160.0,
        "treatment": 168.0,
        "lift": 8.0,
        "ci": (3.0, 13.0),
        "p": 0.001,
    },
    "aov_adjusted": AOV_ADJUSTED,
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
    r["aov_adjusted"] = {**AOV_ADJUSTED, "ci": (-13.0, -3.0)}
    assert "DO NOT SHIP" in generate_report(r)


def test_need_more_data_when_ci_spans_zero():
    r = dict(RESULTS)
    r["aov"] = {**RESULTS["aov"], "lift": 1.0, "ci": (-2.0, 4.0)}
    r["aov_adjusted"] = {**AOV_ADJUSTED, "ci": (-2.0, 4.0)}
    assert "NEED MORE DATA" in generate_report(r)


def test_report_includes_adjusted_row():
    md = generate_report(RESULTS)
    assert "AOV (covariate-adjusted)" in md
    assert "variance" in md.lower()


def test_scenarios_report_has_adjusted_columns():
    scenarios = [
        {
            "scenario": "large",
            "simulated_effect": 0.05,
            "aov": {
                "control": 100.0,
                "treatment": 105.0,
                "lift": 5.0,
                "ci": (3.0, 7.0),
                "p": 0.001,
            },
            "aov_adjusted": AOV_ADJUSTED,
            "verdict": "SHIP",
        },
    ]
    md = generate_scenarios_report(scenarios)
    assert "Adj. lift" in md


def test_verdict_uses_adjusted_ci():
    # unadjusted CI spans zero → NEED MORE DATA if unadjusted were used
    # adjusted CI is positive → SHIP
    r = dict(RESULTS)
    r["aov"] = {**RESULTS["aov"], "lift": 1.0, "ci": (-1.0, 5.0)}
    r["aov_adjusted"] = {**AOV_ADJUSTED, "ci": (1.0, 5.0)}
    md = generate_report(r)
    assert "SHIP" in md


def test_sample_sizes_rendered():
    md = generate_report(RESULTS)
    assert "49575" in md and "49866" in md


def test_report_mentions_installment_framing():
    # use the same results dict as test_report_includes_adjusted_row
    md = generate_report(RESULTS)
    assert "installment-expansion test" in md
    assert "experiment_001_readout.md" in md


def test_scenarios_report_mentions_installment_framing():
    # use the same scenarios list as test_scenarios_report_has_adjusted_columns
    scenarios = [
        {
            "scenario": "large",
            "simulated_effect": 0.05,
            "aov": {
                "control": 100.0,
                "treatment": 105.0,
                "lift": 5.0,
                "ci": (3.0, 7.0),
                "p": 0.001,
            },
            "aov_adjusted": AOV_ADJUSTED,
            "verdict": "SHIP",
        },
    ]
    md = generate_scenarios_report(scenarios)
    assert "installment-expansion test" in md


def test_scenarios_report_lists_all_verdicts():
    scenarios = [
        {
            "scenario": "null",
            "simulated_effect": 0.0,
            "aov": {
                "control": 100.0,
                "treatment": 100.1,
                "lift": 0.1,
                "ci": (-2.0, 2.2),
                "p": 0.9,
            },
            "aov_adjusted": {**AOV_ADJUSTED, "ci": (-2.0, 2.2)},
            "verdict": "NEED MORE DATA",
        },
        {
            "scenario": "large",
            "simulated_effect": 0.05,
            "aov": {
                "control": 100.0,
                "treatment": 105.0,
                "lift": 5.0,
                "ci": (3.0, 7.0),
                "p": 0.001,
            },
            "aov_adjusted": {**AOV_ADJUSTED, "ci": (3.0, 7.0)},
            "verdict": "SHIP",
        },
    ]
    md = generate_scenarios_report(scenarios)
    assert "null" in md and "large" in md
    assert "NEED MORE DATA" in md and "SHIP" in md
    assert "simulated" in md.lower()
