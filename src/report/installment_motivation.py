"""Descriptive installment stats that motivate the installment-expansion framing.

Observational only: shows the affordability mechanism exists in Olist (installment
usage and AOV-by-installment gradient). It does NOT estimate the treatment effect —
that is the simulated experiment's job. See ADR 0008.
"""

from pathlib import Path
from typing import Any

import duckdb

from src._sql import load_sql
from src.constants import COHORT_END_EXCLUSIVE, COHORT_START
from src.io.loader import load_olist
from src.report.results_io import results_to_json

RAW_DIR = Path("data/raw/olist")
MD_PATH = Path("reports/installment_motivation.md")
JSON_PATH = Path("reports/installment_motivation.json")

_WINDOW = {"start": COHORT_START, "end": COHORT_END_EXCLUSIVE}


def compute_motivation_stats(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    buckets_df = con.execute(load_sql("eda/installments.sql"), _WINDOW).fetchdf()
    row = con.execute(load_sql("eda/installments_cc.sql"), _WINDOW).fetchone()
    cc_share = float(row[0]) if row is not None else 0.0
    buckets: list[dict[str, object]] = [
        {
            "bucket": str(r["bucket"]),
            "n_orders": int(r["n_orders"]),
            "aov": float(r["aov"]),
        }
        for r in buckets_df.to_dict("records")
    ]
    n_total = sum(int(b["n_orders"]) for b in buckets)  # type: ignore[call-overload]
    n_single = next((int(b["n_orders"]) for b in buckets if b["bucket"] == "1"), 0)  # type: ignore[call-overload]
    return {
        "cohort_window": [COHORT_START, COHORT_END_EXCLUSIVE],
        "n_orders": n_total,
        "buckets": buckets,
        "share_multi_installment_orders": (n_total - n_single) / n_total,
        "credit_card_value_share": cc_share,
    }


def generate_motivation_md(stats: dict[str, Any]) -> str:
    lines = [
        "# Installment Usage — Motivation Stats (Descriptive)",
        "",
        "> **Descriptive / observational.** These numbers show the affordability mechanism",
        "> exists in Olist (installment usage is common and AOV rises with installment count).",
        "> They are **not an effect estimate** — the simulated experiment estimates the effect.",
        "",
        f"Cohort window: {stats['cohort_window'][0]} → {stats['cohort_window'][1]} "
        f"({stats['n_orders']} orders).",
        "",
        "| Installments | Orders | AOV |",
        "|---|---|---|",
    ]
    for b in stats["buckets"]:
        lines.append(f"| {b['bucket']} | {b['n_orders']} | {b['aov']:.2f} |")
    lines += [
        "",
        f"- Orders paid in >1 installment: **{stats['share_multi_installment_orders']:.1%}**",
        f"- Credit card share of payment value: **{stats['credit_card_value_share']:.1%}**",
        "",
    ]
    return "\n".join(lines)


def write_motivation_outputs(
    stats: dict[str, Any], md_path: Path, json_path: Path
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(generate_motivation_md(stats))
    json_path.write_text(results_to_json(stats) + "\n")


def main(
    raw_dir: Path = RAW_DIR,
    md_path: Path = MD_PATH,
    json_path: Path = JSON_PATH,
) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    write_motivation_outputs(compute_motivation_stats(con), md_path, json_path)
    print(f"wrote {md_path} and {json_path}")


if __name__ == "__main__":
    main()
