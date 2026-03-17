from datetime import date

from app.models.credit_card import CreditCard
from app.services.credit_card_bill import calc_first_period_date, calc_billing_period


def _create_card(client, name="測試卡", billing_day=15, due_day=3):
    resp = client.post("/api/v1/credit-cards", json={
        "name": name, "billing_day": billing_day, "due_day": due_day,
    })
    return resp.json()["data"]["id"]


def test_create_installment_obligation(client):
    """建立 type=installment 的 Obligation 時自動建立 Installment"""
    card_id = _create_card(client)
    resp = client.post("/api/v1/obligations", json={
        "name": "iPhone 分期",
        "type": "installment",
        "amount": 2500,  # 每月 2,500 元
        "frequency": "monthly",
        "start_date": "2026-03-01",
        "installment": {
            "credit_card_id": card_id,
            "total_amount": 30000,
            "total_periods": 12,
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["type"] == "installment"
    assert data["installment"] is not None
    assert data["installment"]["total_amount"] == 30000
    assert data["installment"]["monthly_amount"] == 2500
    assert data["installment"]["total_periods"] == 12
    assert data["installment"]["remaining_periods"] == 12
    assert data["installment"]["credit_card_id"] == card_id


def test_installment_requires_detail(client):
    """type=installment 但未提供 installment 明細應 422"""
    resp = client.post("/api/v1/obligations", json={
        "name": "Bad",
        "type": "installment",
        "amount": 1000,
        "frequency": "monthly",
        "start_date": "2026-03-01",
    })
    assert resp.status_code == 422


def test_non_installment_rejects_detail(client):
    """非 installment 類型不可提供 installment 明細"""
    card_id = _create_card(client)
    resp = client.post("/api/v1/obligations", json={
        "name": "Bad",
        "type": "fixed",
        "amount": 1000,
        "frequency": "monthly",
        "start_date": "2026-03-01",
        "installment": {
            "credit_card_id": card_id,
            "total_amount": 12000,
            "total_periods": 12,
        },
    })
    assert resp.status_code == 422


def test_list_obligations_includes_installment(client):
    """列出 obligations 時 type=installment 包含 nested installment"""
    card_id = _create_card(client)
    client.post("/api/v1/obligations", json={
        "name": "分期",
        "type": "installment",
        "amount": 2500,
        "frequency": "monthly",
        "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })
    resp = client.get("/api/v1/obligations?type=installment")
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["installment"] is not None


def test_delete_obligation_cascades_installment(client, db):
    """刪除 obligation 級聯刪除 installment"""
    from app.models.installment import Installment

    card_id = _create_card(client)
    resp = client.post("/api/v1/obligations", json={
        "name": "分期",
        "type": "installment",
        "amount": 2500,
        "frequency": "monthly",
        "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })
    ob_id = resp.json()["data"]["id"]
    assert db.query(Installment).count() == 1

    client.delete(f"/api/v1/obligations/{ob_id}")
    assert db.query(Installment).count() == 0


def test_calc_first_period_date():
    """首期扣款日計算"""
    # start_date 在 billing_day 之前 → 同月
    assert calc_first_period_date(date(2026, 3, 1), 15) == date(2026, 3, 15)
    # start_date 在 billing_day 之後 → 下月
    assert calc_first_period_date(date(2026, 3, 20), 15) == date(2026, 4, 15)
    # start_date 等於 billing_day → 同月
    assert calc_first_period_date(date(2026, 3, 15), 15) == date(2026, 3, 15)
    # 12月跨年
    assert calc_first_period_date(date(2026, 12, 20), 15) == date(2027, 1, 15)


def test_calc_billing_period():
    """帳單結帳區間計算"""
    start, end = calc_billing_period(2026, 3, 15)
    assert start == date(2026, 2, 16)
    assert end == date(2026, 3, 15)
