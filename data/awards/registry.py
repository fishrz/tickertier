"""Award registry: maps award_code → (compute_fn, supported_periods, group)."""
from __future__ import annotations

from importlib import import_module
from typing import Callable

# code → (module path relative to data.awards, periods supported, group)
_AWARDS: dict[str, tuple[str, list[str], str]] = {
    # Daily
    "daily_king": ("daily.daily_king", ["D"], "daily"),
    "daily_clown": ("daily.daily_clown", ["D"], "daily"),
    "roller_coaster": ("daily.roller_coaster", ["D"], "daily"),
    "oscar": ("daily.oscar", ["D"], "daily"),
    "comeback": ("daily.comeback", ["D"], "daily"),
    "npc_god": ("daily.npc_god", ["D"], "daily"),
    "pump_army": ("daily.pump_army", ["D"], "daily"),
    "tank": ("daily.tank", ["D"], "daily"),
    # Periodic
    "reverse_idx": ("periodic.reverse_idx", ["W", "M", "Q", "H", "Y"], "periodic"),
    "steady_grind": ("periodic.steady_grind", ["W", "M", "Q", "H", "Y"], "periodic"),
    "gambler": ("periodic.gambler", ["W", "M", "Q", "H", "Y"], "periodic"),
    "workhorse": ("periodic.workhorse", ["M", "Q", "Y"], "periodic"),
    "silver_curse": ("periodic.silver_curse", ["M", "Q", "Y"], "periodic"),
    # Earnings
    "earnings_god": ("periodic.earnings_god", ["E"], "periodic"),
    "earnings_clown": ("periodic.earnings_clown", ["E"], "periodic"),
    # Portfolio
    "pillar": ("portfolio.pillar", ["D"], "portfolio"),
    "traitor": ("portfolio.traitor", ["D"], "portfolio"),
}


def list_awards() -> list[str]:
    return list(_AWARDS.keys())


def get_award(code: str) -> tuple[Callable, list[str], str]:
    mod_path, periods, group = _AWARDS[code]
    mod = import_module(f"data.awards.{mod_path}")
    return mod.compute, periods, group


def awards_for_period(period: str) -> list[str]:
    return [c for c, (_m, ps, _g) in _AWARDS.items() if period in ps]
