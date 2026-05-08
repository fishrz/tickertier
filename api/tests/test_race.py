def test_race_cum_return(fake_db):
    r = fake_db.get("/race?metric=cum_return&period=W")
    assert r.status_code == 200
    j = r.json()
    assert j["metric"] == "cum_return"
    assert len(j["frames"]) > 0
    f0 = j["frames"][-1]
    assert "date" in f0
    assert len(f0["entries"]) > 0
    assert "ticker" in f0["entries"][0]
    assert "value" in f0["entries"][0]
    assert "rank" in f0["entries"][0]


def test_race_medals(fake_db):
    r = fake_db.get("/race?metric=medals&period=D")
    assert r.status_code == 200
    j = r.json()
    assert j["metric"] == "medals"
    assert len(j["frames"]) > 0


def test_race_bad_metric(fake_db):
    r = fake_db.get("/race?metric=bogus")
    assert r.status_code == 400
