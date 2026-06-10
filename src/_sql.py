"""Locate and read versioned SQL files."""

from pathlib import Path

SQL_DIR: Path = Path(__file__).resolve().parent.parent / "sql"


def load_sql(rel: str) -> str:
    return (SQL_DIR / rel).read_text()
