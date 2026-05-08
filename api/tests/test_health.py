def test_health(fake_db):
    r = fake_db.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["as_of"] == "2026-05-08"
