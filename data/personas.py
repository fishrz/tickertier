"""KMeans-based 8-persona clustering of tickers using their 3-year tier distribution."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import duckdb
import numpy as np
from sklearn.cluster import KMeans

from data.awards.registry import BENCHMARK_TICKERS
from data.db import get_conn

TIERS: list[str] = ["👑 顶级", "🔥 夯死了", "💪 人上人", "😐 NPC", "💩 拉完了", "☠️ 答辩"]


def _tier_matrix(con: duckdb.DuckDBPyConnection) -> tuple[list[str], np.ndarray]:
    bench = ",".join(f"'{t}'" for t in BENCHMARK_TICKERS) or "''"
    rows = con.execute(
        f"""
        SELECT ticker, tier, COUNT(*) AS n
        FROM tiers
        WHERE ticker NOT IN ({bench})
        GROUP BY ticker, tier
        """
    ).fetchall()
    by_t: dict[str, dict[str, int]] = {}
    for tk, tier, n in rows:
        by_t.setdefault(tk, {})[tier] = int(n)
    tickers = sorted(by_t.keys())
    mat = np.zeros((len(tickers), len(TIERS)), dtype=float)
    for i, tk in enumerate(tickers):
        d = by_t[tk]
        total = sum(d.values()) or 1
        for j, tier in enumerate(TIERS):
            mat[i, j] = d.get(tier, 0) / total
    return tickers, mat


# Persona scoring heuristics. Each takes a centroid (6,) and returns a score; higher = better fit.
# Indices: 0=顶级, 1=夯死了, 2=人上人, 3=NPC, 4=拉完了, 5=答辩
def _score_personas(c: np.ndarray) -> dict[str, float]:
    top, hot, up, npc, down, trash = c[0], c[1], c[2], c[3], c[4], c[5]
    var = float(np.var(c))
    extreme = hot + trash  # high in both hot AND trash → dramatic swings
    return {
        "夯系顶流":   (hot + top) - 0.5 * (down + trash),
        "过山车选手": hot + trash - 0.5 * abs(hot - trash),  # high in both
        "蒸蒸日上":   up - (hot + trash),
        "NPC 系":     npc - 0.5 * (hot + trash + top),
        "长期病号":   down + trash - 0.5 * (top + hot),
        "老油条":     (hot + up) - abs(hot - up) - (top + trash),
        "财报戏精":   var * 4 + extreme,
        "隐藏 boss":  -var * 3 - abs(c.sum() / len(c) - c).sum(),  # near-uniform / low signal
    }


def _assign_personas(centroids: np.ndarray) -> list[str]:
    """For each cluster centroid pick the persona with the highest score (alphabetic tie-break)."""
    out: list[str] = []
    for c in centroids:
        scores = _score_personas(c)
        best = max(scores.items(), key=lambda kv: (kv[1], -ord(kv[0][0])))
        out.append(best[0])
    return out


def compute_personas(con: duckdb.DuckDBPyConnection, k: int = 8) -> int:
    """Cluster tickers into k personas based on tier-distribution and write to personas table.

    Returns the number of rows written.
    """
    tickers, mat = _tier_matrix(con)
    if not tickers:
        return 0
    k = min(k, len(tickers))
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(mat)
    persona_for_cluster = _assign_personas(km.cluster_centers_)

    now = datetime.now(timezone.utc)
    con.execute("DELETE FROM personas")
    rows = []
    for i, tk in enumerate(tickers):
        dist = {TIERS[j]: float(mat[i, j]) for j in range(len(TIERS))}
        rows.append((tk, persona_for_cluster[labels[i]], json.dumps(dist, ensure_ascii=False), now))
    con.executemany(
        "INSERT INTO personas (ticker, persona, tier_dist, updated_at) VALUES (?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def main() -> None:
    con = get_conn(read_only=False)
    try:
        n = compute_personas(con)
        print(f"Wrote {n} personas.")
        rows = con.execute(
            "SELECT persona, COUNT(*) AS n FROM personas GROUP BY persona ORDER BY n DESC"
        ).fetchall()
        print("Persona sizes:")
        for p, c in rows:
            print(f"  {p}: {c}")
        sample = con.execute(
            "SELECT ticker, persona FROM personas ORDER BY ticker LIMIT 5"
        ).fetchall()
        print("Sample:")
        for tk, p in sample:
            print(f"  {tk} → {p}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
