from pathlib import Path

import duckdb
import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def base_con():
    """In-memory DuckDB with the raw Olist base tables registered from fixtures."""
    con = duckdb.connect(":memory:")
    for name in ["customers", "orders", "order_payments", "order_items"]:
        df = pd.read_csv(FIXTURES / f"{name}.csv")
        if "timestamp" in "".join(df.columns):
            for col in df.columns:
                if col.endswith("timestamp"):
                    df[col] = pd.to_datetime(df[col])
        con.register(name, df)
    yield con
    con.close()


@pytest.fixture
def frame() -> pd.DataFrame:
    df = pd.read_csv(FIXTURES / "experiment_frame.csv")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df


@pytest.fixture
def frame_con(frame):
    """In-memory DuckDB with the experiment_frame registered for metric SQL."""
    con = duckdb.connect(":memory:")
    con.register("experiment_frame", frame)
    yield con
    con.close()
