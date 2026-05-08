"""FastAPI app entrypoint."""
from __future__ import annotations

import duckdb
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_db
from api.routes import awards, portfolio, race, stocks
from data.db import DB_PATH

app = FastAPI(title="Stock Awards API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> dict:
    row = con.execute("SELECT MAX(date) FROM prices").fetchone()
    as_of = str(row[0]) if row and row[0] else None
    return {"status": "ok", "db_path": str(DB_PATH), "as_of": as_of}


app.include_router(awards.router)
app.include_router(stocks.router)
app.include_router(race.router)
app.include_router(portfolio.router)
