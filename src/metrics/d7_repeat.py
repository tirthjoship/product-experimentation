"""D7 repeat-purchase rate per variant. Definition lives in sql/metrics/d7_repeat.sql."""

import duckdb

from src._sql import load_sql


def d7_repeat_by_variant(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = con.execute(load_sql("metrics/d7_repeat.sql")).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}
