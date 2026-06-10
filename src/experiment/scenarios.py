"""Sweep the injected effect across scenarios to validate the decision rule."""

from typing import cast

import duckdb

from src.constants import SCENARIOS
from src.experiment.run_experiment import run
from src.report.experiment_report import recommend


def run_scenarios(
    con: duckdb.DuckDBPyConnection,
    scenarios: tuple[tuple[str, float], ...] = SCENARIOS,
) -> list[dict[str, object]]:
    """Run the experiment once per scenario; tag each with its name and verdict."""
    out: list[dict[str, object]] = []
    for name, effect in scenarios:
        result = run(con, effect=effect)
        result["scenario"] = name
        aov = cast("dict[str, object]", result["aov"])
        result["verdict"] = recommend(cast("tuple[float, float]", aov["ci"]))
        out.append(result)
    return out
