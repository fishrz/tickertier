"""DuckDB connection helpers and universe loader."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "awards.duckdb"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
UNIVERSE_PATH = Path(__file__).parent / "universe.json"


def get_conn(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the project database.

    Example:
        >>> con = get_conn()
        >>> con.execute("SELECT 1").fetchone()
        (1,)
    """
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Apply schema.sql to the given connection (idempotent).

    Example:
        >>> con = duckdb.connect(":memory:")
        >>> init_schema(con)
    """
    sql = SCHEMA_PATH.read_text()
    con.execute(sql)


def universe() -> list[dict]:
    """Load the AI infrastructure ticker universe from universe.json.

    Example:
        >>> u = universe()
        >>> u[0]["ticker"]
        'NVDA'
    """
    return json.loads(UNIVERSE_PATH.read_text())
