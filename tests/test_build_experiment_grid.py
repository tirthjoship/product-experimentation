"""Tests for scripts/build_experiment_grid.py — uses tiny fixture, never full Olist."""

import json

from scripts.build_experiment_grid import build_grid


def test_build_grid_shape(base_con) -> None:  # reuses the shared duckdb fixture
    rows = build_grid(base_con, pct_lo=-2, pct_hi=2, step=1)
    assert len(rows) == 5  # -2, -1, 0, 1, 2
    effects = [r["simulated_effect"] for r in rows]
    assert effects == [-0.02, -0.01, 0.0, 0.01, 0.02]
    for r in rows:
        assert "aov_adjusted" in r
        assert "verdict" in r
        assert "scenario" in r


def test_build_grid_scenario_names(base_con) -> None:
    rows = build_grid(base_con, pct_lo=0, pct_hi=1, step=1)
    assert rows[0]["scenario"] == "eff_+0"
    assert rows[1]["scenario"] == "eff_+1"


def test_build_grid_rows_are_dicts(base_con) -> None:
    rows = build_grid(base_con, pct_lo=0, pct_hi=0, step=1)
    assert len(rows) == 1
    # Must be JSON-serialisable (same schema as experiment_scenarios.json)
    serialised = json.dumps(rows, default=str)
    assert isinstance(serialised, str)
