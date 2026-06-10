"""Load Olist into DuckDB and build the cohort experiment frame."""

from pathlib import Path

import duckdb
import pandas as pd

from src._sql import load_sql
from src.constants import COHORT_END_EXCLUSIVE, COHORT_START
from src.exceptions import EmptyCohortError
from src.experiment.assignment import assign_variant

_TABLES = ["orders", "order_items", "order_payments", "customers"]


def load_olist(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    """Register the raw Olist CSVs as DuckDB views (parses timestamp columns)."""
    for name in _TABLES:
        df = pd.read_csv(raw_dir / f"olist_{name}_dataset.csv")
        for col in df.columns:
            if col.endswith("timestamp"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
        con.register(name, df)


def build_experiment_frame(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.execute(
        load_sql("experiment/cohort.sql"),
        {"start": COHORT_START, "end": COHORT_END_EXCLUSIVE},
    ).fetchdf()
    if df.empty:
        raise EmptyCohortError("cohort filter returned zero rows")
    df["variant"] = df["customer_unique_id"].map(assign_variant)
    return df
