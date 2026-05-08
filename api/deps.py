"""FastAPI dependencies — DB connection lifecycle."""
from __future__ import annotations

from typing import Iterator

import duckdb

from data.db import DB_PATH


def get_db() -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield a fresh read-only DuckDB connection per request."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        yield con
    finally:
        con.close()
