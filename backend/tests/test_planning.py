from datetime import date

from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.services.planning import evaluate_spend


def test_can_spend_feasible(db):
    """花費後仍有餘裕 → is_feasible=True"""
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    db.add(Obligation(
        name="生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.commit()

    result = evaluate_spend(db, amount_cents=500000, as_of=date(2026, 3, 14))

    assert result["is_feasible"] is True
    assert result["available_before"] > result["available_after"]
    assert result["available_after"] == result["available_before"] - 500000


def test_can_spend_not_feasible(db):
    """花費後餘額為負 → is_feasible=False"""
    db.add(Account(name="銀行", type="bank", balance=100000, currency="TWD"))
    db.add(Obligation(
        name="生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.commit()

    result = evaluate_spend(db, amount_cents=500000, as_of=date(2026, 3, 14))

    assert result["is_feasible"] is False


def test_can_spend_zero_boundary(db):
    """花費後剛好為 0 → is_feasible=True（不是負數就算可行）"""
    # 帳戶 10,000 分 = 100 元，無義務
    db.add(Account(name="銀行", type="bank", balance=10000, currency="TWD"))
    db.commit()

    result = evaluate_spend(db, amount_cents=10000, as_of=date(2026, 3, 14))
    assert result["is_feasible"] is True
    assert result["available_after"] == 0


def test_can_i_spend_endpoint_feasible(client, db):
    """POST /planning/can-i-spend 成功回應"""
    from app.models.account import Account
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    db.commit()

    resp = client.post("/api/v1/planning/can-i-spend", json={
        "amount": 5000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_feasible"] is True
    assert data["available_before"] == 100000.0
    assert data["available_after"] == 95000.0
    assert "可行" in data["summary"]


def test_can_i_spend_endpoint_not_feasible(client, db):
    """POST /planning/can-i-spend 超支"""
    from app.models.account import Account
    db.add(Account(name="銀行", type="bank", balance=100000, currency="TWD"))
    db.commit()

    resp = client.post("/api/v1/planning/can-i-spend", json={
        "amount": 5000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_feasible"] is False
    assert "超支" in data["summary"]


def test_can_i_spend_validation_error(client):
    """amount <= 0 → 422"""
    resp = client.post("/api/v1/planning/can-i-spend", json={
        "amount": -100,
    })
    assert resp.status_code == 422
