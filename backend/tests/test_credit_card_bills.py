from datetime import date

from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.obligation import Obligation
from app.models.installment import Installment


def _create_card(client, billing_day=15, due_day=3):
    resp = client.post("/api/v1/credit-cards", json={
        "name": "測試卡", "billing_day": billing_day, "due_day": due_day,
    })
    return resp.json()["data"]["id"]


def test_create_bill(client):
    card_id = _create_card(client)
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026,
        "billing_month": 3,
        "due_date": "2026-04-03",
        "general_spending": 6000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["credit_card_id"] == card_id
    assert data["billing_year"] == 2026
    assert data["billing_month"] == 3
    assert data["general_spending"] == 6000.0
    assert data["installment_amount"] == 0  # no installments
    assert data["total_amount"] == 6000.0
    assert data["is_paid"] is False


def test_duplicate_bill_409(client):
    """#11: 同卡同月不能建兩筆帳單"""
    card_id = _create_card(client)
    client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 5000,
    })
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 3000,
    })
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "DUPLICATE_BILL"


def test_installment_amount_aggregation(client, db):
    """#10: installment_amount 從 Installment 表即時聚合"""
    card_id = _create_card(client, billing_day=15, due_day=3)

    # 建立兩筆分期，current_period_date 落在 3 月帳單區間 (2/16~3/15)
    client.post("/api/v1/obligations", json={
        "name": "iPhone", "type": "installment", "amount": 2500,
        "frequency": "monthly", "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })
    client.post("/api/v1/obligations", json={
        "name": "MacBook", "type": "installment", "amount": 1800,
        "frequency": "monthly", "start_date": "2026-03-10",
        "installment": {"credit_card_id": card_id, "total_amount": 21600, "total_periods": 12},
    })

    # 建立 3 月帳單
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 6000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["installment_amount"] == 4300.0  # 2500 + 1800
    assert data["general_spending"] == 6000.0
    assert data["total_amount"] == 10300.0  # 4300 + 6000


def test_update_bill_mark_paid(client):
    card_id = _create_card(client)
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 5000,
    })
    bill_id = resp.json()["data"]["id"]
    resp = client.put(f"/api/v1/credit-card-bills/{bill_id}", json={"is_paid": True})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_paid"] is True


def test_list_bills_filter(client):
    card_id = _create_card(client)
    client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 5000,
    })
    client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 4,
        "due_date": "2026-05-03", "general_spending": 3000,
    })
    resp = client.get(f"/api/v1/credit-card-bills?credit_card_id={card_id}&billing_month=3")
    assert len(resp.json()["data"]) == 1


def test_delete_bill(client):
    card_id = _create_card(client)
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 5000,
    })
    bill_id = resp.json()["data"]["id"]
    resp = client.delete(f"/api/v1/credit-card-bills/{bill_id}")
    assert resp.status_code == 200
