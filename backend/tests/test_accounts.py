def test_create_account(client):
    resp = client.post("/api/v1/accounts", json={
        "name": "薪轉帳戶",
        "type": "bank",
        "balance": 80000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "薪轉帳戶"
    assert data["type"] == "bank"
    assert data["balance"] == 80000.0


def test_create_account_empty_name_fails(client):
    resp = client.post("/api/v1/accounts", json={
        "name": "",
        "type": "bank",
    })
    assert resp.status_code == 422


def test_list_accounts(client):
    client.post("/api/v1/accounts", json={"name": "A", "type": "bank", "balance": 100})
    client.post("/api/v1/accounts", json={"name": "B", "type": "cash", "balance": 200})
    resp = client.get("/api/v1/accounts")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_update_account(client):
    create = client.post("/api/v1/accounts", json={"name": "A", "type": "bank", "balance": 100})
    aid = create.json()["data"]["id"]
    resp = client.put(f"/api/v1/accounts/{aid}", json={"balance": 999.99})
    assert resp.status_code == 200
    assert resp.json()["data"]["balance"] == 999.99


def test_delete_account(client):
    create = client.post("/api/v1/accounts", json={"name": "A", "type": "bank"})
    aid = create.json()["data"]["id"]
    resp = client.delete(f"/api/v1/accounts/{aid}")
    assert resp.status_code == 200
    resp = client.get("/api/v1/accounts")
    assert len(resp.json()["data"]) == 0


def test_delete_nonexistent_account(client):
    resp = client.delete("/api/v1/accounts/999")
    assert resp.status_code == 404
