from datetime import date, datetime, timedelta

from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill


def test_dashboard_summary_basic(client, db):
    """#12: dashboard/summary 基礎功能"""
    db.add(Account(name="主要帳戶", type="bank", balance=8000000, currency="TWD"))
    db.add(Income(
        name="薪水", amount=5000000, frequency="monthly",
        start_date=date(2026, 1, 5), next_date=date(2026, 4, 5),
    ))
    db.commit()

    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_balance"] == 80000.0
    assert "available_amount" in data
    assert "accounts" in data
    assert "upcoming_dues" in data
    assert "stale_accounts" in data


def test_dashboard_stale_accounts(client, db):
    """餘額超過 7 天未更新的帳戶出現在 stale_accounts"""
    stale_time = datetime.now() - timedelta(days=10)
    db.add(Account(
        name="舊帳戶", type="bank", balance=1000000, currency="TWD",
        balance_updated_at=stale_time,
    ))
    db.commit()

    resp = client.get("/api/v1/dashboard/summary")
    data = resp.json()["data"]
    assert len(data["stale_accounts"]) == 1
    assert data["stale_accounts"][0]["name"] == "舊帳戶"


def test_batch_update_balances(client):
    """PATCH /accounts/batch-update-balances"""
    r1 = client.post("/api/v1/accounts", json={"name": "A", "type": "bank", "balance": 1000})
    r2 = client.post("/api/v1/accounts", json={"name": "B", "type": "bank", "balance": 2000})
    id1 = r1.json()["data"]["id"]
    id2 = r2.json()["data"]["id"]

    resp = client.patch("/api/v1/accounts/batch-update-balances", json={
        "updates": [
            {"id": id1, "balance": 5000},
            {"id": id2, "balance": 8000},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    balances = {d["id"]: d["balance"] for d in data}
    assert balances[id1] == 5000.0
    assert balances[id2] == 8000.0


def test_batch_update_not_found(client):
    resp = client.patch("/api/v1/accounts/batch-update-balances", json={
        "updates": [{"id": 999, "balance": 1000}]
    })
    assert resp.status_code == 404
