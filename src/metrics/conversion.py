"""Conversion (delivered rate) per variant. Definition lives in sql/metrics/conversion.sql."""

import duckdb

from src._sql import load_sql


def conversion_by_variant(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = con.execute(load_sql("metrics/conversion.sql")).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}
