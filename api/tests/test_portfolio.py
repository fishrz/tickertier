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
