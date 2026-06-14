"""Offline: sweep the injected effect across a fine grid for the What-if tab.

Reuses the exact experiment machinery (run_scenarios + results_to_json) so each
grid point has the same schema as reports/experiment_scenarios.json. NOT run in
the app or in pytest against full data — it loads full Olist and runs the full
experiment (incl. 10k bootstrap) once per grid point (minutes, not seconds).
"""

from pathlib import Path

import duckdb

from src.experiment.run_experiment import RAW_DIR
from src.experiment.scenarios import run_scenarios
from src.io.loader import load_olist
from src.report.results_io import results_to_json

GRID_JSON_PATH = Path("reports/experiment_grid.json")


def _grid(pct_lo: int, pct_hi: int, step: int) -> tuple[tuple[str, float], ...]:
    return tuple(
        (f"eff_{pct:+d}", pct / 100.0) for pct in range(pct_lo, pct_hi + 1, step)
    )


def build_grid(
    con: duckdb.DuckDBPyConnection,
    pct_lo: int = -10,
    pct_hi: int = 10,
    step: int = 1,
) -> list[dict[str, object]]:
    """Run the experiment once per grid point; return list of result dicts.

    Pure of file IO so tests can call it with a fixture connection.
    """
    return run_scenarios(con, _grid(pct_lo, pct_hi, step))


def main(raw_dir: Path = RAW_DIR, out_path: Path = GRID_JSON_PATH) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    rows = build_grid(con)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(results_to_json(rows) + "\n")
    print(f"wrote {out_path} ({len(rows)} points)")


if __name__ == "__main__":
    main()
