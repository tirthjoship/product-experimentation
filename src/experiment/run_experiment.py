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
from src.report.experiment_report import generate_report

RAW_DIR = Path("data/raw/olist")
REPORT_PATH = Path("reports/experiment_001.md")


def run(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    frame = build_experiment_frame(con)
    check_balance(frame)
    injected = apply_simulated_effect(frame)
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
        "simulated_effect": SIMULATED_EFFECT,
        "alpha": ALPHA,
    }


def main() -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, RAW_DIR)
    results = run(con)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(generate_report(results))
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
