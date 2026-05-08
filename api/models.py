"""Pydantic response models."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AwardWinner(BaseModel):
    rank: int
    ticker: str
    metric: float
    meta: dict[str, Any] = {}


class AwardGroup(BaseModel):
    code: str
    name: str
    description: str
    winners: list[AwardWinner]


class TodayAwards(BaseModel):
    date: str
    awards: list[AwardGroup]
    tier_distribution: dict[str, int]


class LeaderboardEntry(BaseModel):
    ticker: str
    persona: str | None = None
    gold: int
    silver: int
    bronze: int
    total: int


class StockProfile(BaseModel):
    ticker: str
    name: str
    theme: str
    persona: str | None = None
    medal_count: dict[str, int]
    tier_distribution: dict[str, float]
    last_close: float
    last_pct_change: float
    recent_30d: list[dict]


class RaceFrame(BaseModel):
    date: str
    entries: list[dict]


class RaceResponse(BaseModel):
    metric: str
    period: str
    frames: list[RaceFrame]


class Position(BaseModel):
    ticker: str
    shares: float
    avg_cost: float
    last_close: float
    market_value: float
    unrealized_pnl: float
    today_pnl: float
    today_pct: float
    tier_today: str | None = None


class PortfolioToday(BaseModel):
    as_of: str
    total_market_value: float
    total_unrealized_pnl: float
    today_pnl: float
    pillar: dict | None = None
    traitor: dict | None = None
    positions: list[Position]
