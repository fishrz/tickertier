def test_stock_profile(fake_db):
    r = fake_db.get("/stocks/NVDA")
    assert r.status_code == 200
    j = r.json()
    assert j["ticker"] == "NVDA"
    assert j["persona"]
    assert j["last_close"] > 0
    assert len(j["recent_30d"]) > 0
    assert "daily_king" in j["medal_count"]
    assert len(j["medal_history"]) > 0
    # medal_history entries have code, name, count, latest_date, best_rank
    mh = j["medal_history"]
    assert any(m["code"] == "daily_king" for m in mh)
    first = mh[0]
    assert "name" in first and "count" in first and "best_rank" in first


def test_stock_profile_404(fake_db):
    r = fake_db.get("/stocks/ZZZZ")
    assert r.status_code == 404


def test_stock_medals(fake_db):
    r = fake_db.get("/stocks/NVDA/medals?period=Y")
    assert r.status_code == 200
    j = r.json()
    assert j["ticker"] == "NVDA"
    assert "workhorse" in j["medals"]


def test_stock_lowercase(fake_db):
    r = fake_db.get("/stocks/nvda")
    assert r.status_code == 200
    assert r.json()["ticker"] == "NVDA"
