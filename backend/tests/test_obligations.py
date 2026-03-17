def test_create_fixed_obligation(client):
    resp = client.post("/api/v1/obligations", json={
        "name": "房租",
        "type": "fixed",
        "amount": 12000,
        "frequency": "monthly",
        "start_date": "2026-01-01",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "房租"
    assert data["type"] == "fixed"
    assert data["amount"] == 12000.0
    assert data["next_due_date"] == "2026-01-01"


def test_create_budget_obligation(client):
    resp = client.post("/api/v1/obligations", json={
        "name": "現金生活費",
        "type": "budget",
        "amount": 8000,
        "frequency": "monthly",
        "start_date": "2026-01-01",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["type"] == "budget"


def test_list_obligations_filter_type(client):
    client.post("/api/v1/obligations", json={
        "name": "房租", "type": "fixed", "amount": 12000,
        "frequency": "monthly", "start_date": "2026-01-01",
    })
    client.post("/api/v1/obligations", json={
        "name": "生活費", "type": "budget", "amount": 8000,
        "frequency": "monthly", "start_date": "2026-01-01",
    })
    resp = client.get("/api/v1/obligations?type=fixed")
    assert len(resp.json()["data"]) == 1
    resp = client.get("/api/v1/obligations")
    assert len(resp.json()["data"]) == 2


def test_update_obligation(client):
    create = client.post("/api/v1/obligations", json={
        "name": "房租", "type": "fixed", "amount": 12000,
        "frequency": "monthly", "start_date": "2026-01-01",
    })
    oid = create.json()["data"]["id"]
    resp = client.put(f"/api/v1/obligations/{oid}", json={"amount": 13000})
    assert resp.json()["data"]["amount"] == 13000.0


def test_delete_obligation(client):
    create = client.post("/api/v1/obligations", json={
        "name": "房租", "type": "fixed", "amount": 12000,
        "frequency": "monthly", "start_date": "2026-01-01",
    })
    oid = create.json()["data"]["id"]
    resp = client.delete(f"/api/v1/obligations/{oid}")
    assert resp.status_code == 200
