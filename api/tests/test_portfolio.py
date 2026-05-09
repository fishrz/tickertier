import pytest


@pytest.fixture(autouse=True)
def _no_lottery(monkeypatch):
    """Test fixture only seeds NVDA/AMD; ensure portfolio.json lottery rows don't bleed in."""
    from api.routes import portfolio
    monkeypatch.setattr(portfolio, "_load_lottery_tickers", lambda: {})


def test_portfolio_today(fake_db):
    r = fake_db.get("/portfolio/today")
    assert r.status_code == 200
    j = r.json()
    assert j["as_of"] == "2026-05-08"
    assert len(j["positions"]) == 2
    tickers = {p["ticker"] for p in j["positions"]}
    assert tickers == {"NVDA", "AMD"}
    assert j["total_market_value"] > 0
    assert j["pillar"] is not None
    assert j["traitor"] is not None
    p0 = j["positions"][0]
    assert p0["last_close"] > 0
    assert p0["tier_today"] is not None
    assert p0["lottery"] is False
