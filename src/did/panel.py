"""Blinded state×week panel builder. Post-period rows exist only after a committed
GO verdict — the verdict JSON is the key (spec §5, §7)."""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src._sql import load_sql
from src.did.catalog import EventDefinition
from src.exceptions import BlindingError

VERDICT_JSON = Path("reports/did_gate_verdict.json")


def require_go(verdict_path: Path, event_name: str) -> None:
    if not verdict_path.exists():
        raise BlindingError(
            f"no gate verdict at {verdict_path}; post-period data stays blinded"
        )
    verdict = json.loads(verdict_path.read_text())
    if verdict.get("event") != event_name or verdict.get("verdict") != "GO":
        raise BlindingError(f"gate verdict is not GO for {event_name!r}: {verdict!r}")


def build_panel(
    con: duckdb.DuckDBPyConnection,
    event: EventDefinition,
    *,
    unblind_post: bool = False,
    verdict_path: Path = VERDICT_JSON,
) -> pd.DataFrame:
    if unblind_post:
        require_go(verdict_path, event.name)
        end = event.estimation_end_exclusive
    else:
        end = event.boundary_date
    df = con.execute(
        load_sql("did/panel.sql"), {"start": event.estimation_start, "end": end}
    ).fetchdf()
    keep = set(event.treated_states) | set(event.control_states)
    df = df[df["customer_state"].isin(keep)].reset_index(drop=True)
    df["treated"] = df["customer_state"].isin(set(event.treated_states))
    df["post"] = df["week"] >= pd.Timestamp(event.boundary_date)
    df["log_orders"] = np.log1p(df["n_orders"])
    return df.sort_values(["customer_state", "week"]).reset_index(drop=True)
