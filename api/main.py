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
    allow_origins=["*"],  # tighten after first deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> dict:
    row = con.execute("SELECT MAX(date) FROM prices").fetchone()
    as_of = str(row[0]) if row and row[0] else None
    return {"status": "ok", "db_path": str(DB_PATH), "as_of": as_of}


@app.get("/api/stats")
def stats(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> dict:
    """Lightweight footer/masthead stats: universe size, award count, data range."""
    universe = con.execute("SELECT COUNT(DISTINCT ticker) FROM prices").fetchone()
    award_codes = con.execute("SELECT COUNT(DISTINCT award_code) FROM awards").fetchone()
    rng = con.execute("SELECT MIN(date), MAX(date) FROM prices").fetchone()
    medals = con.execute("SELECT COUNT(*) FROM awards").fetchone()
    return {
        "universe": int(universe[0]) if universe else 0,
        "awards": int(award_codes[0]) if award_codes else 0,
        "medals_awarded": int(medals[0]) if medals else 0,
        "data_from": str(rng[0]) if rng and rng[0] else None,
        "data_to": str(rng[1]) if rng and rng[1] else None,
    }


app.include_router(awards.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(race.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
