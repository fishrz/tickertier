def test_today(fake_db):
    r = fake_db.get("/awards/today")
    assert r.status_code == 200
    j = r.json()
    assert j["date"] == "2026-05-08"
    codes = {g["code"] for g in j["awards"]}
    assert "daily_king" in codes
    assert sum(j["tier_distribution"].values()) > 0
    king = next(g for g in j["awards"] if g["code"] == "daily_king")
    assert king["name"].startswith("🏆")
    assert len(king["winners"]) == 3
    assert king["winners"][0]["ticker"] == "NVDA"


def test_period_awards(fake_db):
    r = fake_db.get("/awards/period/Y/2026")
    assert r.status_code == 200
    j = r.json()
    assert any(g["code"] == "workhorse" for g in j["awards"])


def test_period_404(fake_db):
    r = fake_db.get("/awards/period/Y/1900")
    assert r.status_code == 404


def test_leaderboard(fake_db):
    r = fake_db.get("/awards/leaderboard?period=D&limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) > 0
    nvda = next(x for x in rows if x["ticker"] == "NVDA")
    assert nvda["gold"] >= 1
    assert nvda["persona"]
