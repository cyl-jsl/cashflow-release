def test_create_credit_card(client):
    resp = client.post("/api/v1/credit-cards", json={
        "name": "LINE Pay 卡",
        "billing_day": 15,
        "due_day": 3,
        "credit_limit": 200000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "LINE Pay 卡"
    assert data["billing_day"] == 15
    assert data["due_day"] == 3
    assert data["credit_limit"] == 200000.0


def test_create_credit_card_validation(client):
    resp = client.post("/api/v1/credit-cards", json={
        "name": "Bad",
        "billing_day": 0,
        "due_day": 29,
    })
    assert resp.status_code == 422


def test_list_credit_cards(client):
    client.post("/api/v1/credit-cards", json={"name": "A", "billing_day": 10, "due_day": 25})
    client.post("/api/v1/credit-cards", json={"name": "B", "billing_day": 15, "due_day": 3})
    resp = client.get("/api/v1/credit-cards")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_update_credit_card(client):
    resp = client.post("/api/v1/credit-cards", json={"name": "Old", "billing_day": 10, "due_day": 25})
    card_id = resp.json()["data"]["id"]
    resp = client.put(f"/api/v1/credit-cards/{card_id}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New"
    assert resp.json()["data"]["billing_day"] == 10  # unchanged


def test_delete_credit_card(client):
    resp = client.post("/api/v1/credit-cards", json={"name": "Del", "billing_day": 10, "due_day": 25})
    card_id = resp.json()["data"]["id"]
    resp = client.delete(f"/api/v1/credit-cards/{card_id}")
    assert resp.status_code == 200
    resp = client.get("/api/v1/credit-cards")
    assert len(resp.json()["data"]) == 0


def test_delete_credit_card_not_found(client):
    resp = client.delete("/api/v1/credit-cards/999")
    assert resp.status_code == 404
