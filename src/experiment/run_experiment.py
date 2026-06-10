"""Assemble the full simulated experiment and write the report."""

from pathlib import Path

import duckdb

from src.constants import ALPHA, DELIVERED_STATUS, SIMULATED_EFFECT
from src.experiment.analysis import (
    bootstrap_ci_diff_means,
    two_proportion_ztest,
    welch_ttest,
)
from src.experiment.balance import check_balance
from src.experiment.effect import apply_simulated_effect
from src.experiment.power import mde_mean, mde_proportion
from src.io.loader import build_experiment_frame, load_olist
from src.metrics.aov import aov_by_variant
from src.metrics.conversion import conversion_by_variant
from src.metrics.d7_repeat import d7_repeat_by_variant
from src.report.experiment_report import generate_report, generate_scenarios_report
from src.report.results_io import results_to_json, write_results_json

RAW_DIR = Path("data/raw/olist")
REPORT_PATH = Path("reports/experiment_001.md")
JSON_PATH = Path("reports/experiment_001.json")
SCENARIOS_REPORT_PATH = Path("reports/experiment_scenarios.md")
SCENARIOS_JSON_PATH = Path("reports/experiment_scenarios.json")


def run(
    con: duckdb.DuckDBPyConnection, effect: float = SIMULATED_EFFECT
) -> dict[str, object]:
    frame = build_experiment_frame(con)
    check_balance(frame)
    injected = apply_simulated_effect(frame, effect=effect)
    con.register("experiment_frame", injected)

    aov = aov_by_variant(con)
    conv = conversion_by_variant(con)
    d7 = d7_repeat_by_variant(con)

    ctrl_vals = injected.loc[injected["variant"] == "control", "order_value"].to_numpy()
    treat_vals = injected.loc[
        injected["variant"] == "treatment", "order_value"
    ].to_numpy()
    ci = bootstrap_ci_diff_means(ctrl_vals, treat_vals)
    _, aov_p = welch_ttest(ctrl_vals, treat_vals)

    counts = injected["variant"].value_counts()
    n_ctrl, n_treat = int(counts["control"]), int(counts["treatment"])
    x_ctrl = int(
        (
            injected["variant"].eq("control")
            & injected["order_status"].eq(DELIVERED_STATUS)
        ).sum()
    )
    x_treat = int(
        (
            injected["variant"].eq("treatment")
            & injected["order_status"].eq(DELIVERED_STATUS)
        ).sum()
    )
    conv_z, conv_p, conv_lo, conv_hi = two_proportion_ztest(
        x_ctrl, n_ctrl, x_treat, n_treat
    )

    return {
        "sample_sizes": {"control": n_ctrl, "treatment": n_treat},
        "aov": {
            "control": aov["control"],
            "treatment": aov["treatment"],
            "lift": aov["treatment"] - aov["control"],
            "ci": ci,
            "p": aov_p,
        },
        "conversion": {
            "control": conv["control"],
            "treatment": conv["treatment"],
            "z": conv_z,
            "p": conv_p,
            "ci": (conv_lo, conv_hi),
        },
        "d7": {
            "control": d7.get("control", 0.0),
            "treatment": d7.get("treatment", 0.0),
        },
        "mde": {
            "aov": mde_mean(
                float(treat_vals.std(ddof=1)) if treat_vals.size > 1 else 0.0, n_treat
            ),
            "conversion": mde_proportion(conv["control"] or 0.0001, n_ctrl),
        },
        "simulated_effect": effect,
        "alpha": ALPHA,
    }


def write_outputs(
    results: dict[str, object], report_path: Path, json_path: Path
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(generate_report(results))
    write_results_json(results, json_path)


def write_scenarios_outputs(
    scenarios: list[dict[str, object]], md_path: Path, json_path: Path
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(generate_scenarios_report(scenarios))
    json_path.write_text(results_to_json(scenarios) + "\n")


def main(
    raw_dir: Path = RAW_DIR,
    report_path: Path = REPORT_PATH,
    json_path: Path = JSON_PATH,
) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    results = run(con)
    write_outputs(results, report_path, json_path)
    print(f"wrote {report_path} and {json_path}")


def main_scenarios(raw_dir: Path = RAW_DIR) -> None:
    from src.experiment.scenarios import run_scenarios  # lazy: avoids circular import

    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    scenarios = run_scenarios(con)
    write_scenarios_outputs(scenarios, SCENARIOS_REPORT_PATH, SCENARIOS_JSON_PATH)
    large = next(s for s in scenarios if s["scenario"] == "large")
    large_clean = {k: v for k, v in large.items() if k not in ("scenario", "verdict")}
    write_outputs(large_clean, REPORT_PATH, JSON_PATH)
    print(
        f"wrote {SCENARIOS_REPORT_PATH}, {SCENARIOS_JSON_PATH}, "
        f"{REPORT_PATH}, {JSON_PATH}"
    )


if __name__ == "__main__":
    import sys

    if "--scenarios" in sys.argv:
        main_scenarios()
    else:
        main()
