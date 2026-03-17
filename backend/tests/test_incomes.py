from datetime import date


def test_create_income(client):
    resp = client.post("/api/v1/incomes", json={
        "name": "薪水",
        "amount": 50000,
        "frequency": "monthly",
        "start_date": "2026-01-05",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "薪水"
    assert data["amount"] == 50000.0
    assert data["next_date"] == "2026-01-05"


def test_create_income_zero_amount_fails(client):
    resp = client.post("/api/v1/incomes", json={
        "name": "X",
        "amount": 0,
        "frequency": "monthly",
        "start_date": "2026-01-01",
    })
    assert resp.status_code == 422


def test_list_incomes(client):
    client.post("/api/v1/incomes", json={
        "name": "薪水", "amount": 50000, "frequency": "monthly", "start_date": "2026-01-05",
    })
    resp = client.get("/api/v1/incomes")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


def test_update_income(client):
    create = client.post("/api/v1/incomes", json={
        "name": "薪水", "amount": 50000, "frequency": "monthly", "start_date": "2026-01-05",
    })
    iid = create.json()["data"]["id"]
    resp = client.put(f"/api/v1/incomes/{iid}", json={"amount": 55000})
    assert resp.status_code == 200
    assert resp.json()["data"]["amount"] == 55000.0


def test_delete_income(client):
    create = client.post("/api/v1/incomes", json={
        "name": "薪水", "amount": 50000, "frequency": "monthly", "start_date": "2026-01-05",
    })
    iid = create.json()["data"]["id"]
    resp = client.delete(f"/api/v1/incomes/{iid}")
    assert resp.status_code == 200
    assert len(client.get("/api/v1/incomes").json()["data"]) == 0
