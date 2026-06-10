"""Average order value per variant. Definition lives in sql/metrics/aov.sql."""

import duckdb

from src._sql import load_sql


def aov_by_variant(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = con.execute(load_sql("metrics/aov.sql")).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}
