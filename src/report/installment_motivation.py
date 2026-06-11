"""Descriptive installment stats that motivate the installment-expansion framing.

Observational only: shows the affordability mechanism exists in Olist (installment
usage and AOV-by-installment gradient). It does NOT estimate the treatment effect —
that is the simulated experiment's job. See ADR 0008.
"""

from pathlib import Path

import duckdb

from src._sql import load_sql
from src.constants import COHORT_END_EXCLUSIVE, COHORT_START

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
