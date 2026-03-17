from datetime import date

from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.installment import Installment
from app.models.obligation import Obligation
from app.services.credit_card_bill import calc_installment_amount
from app.services.cycle_advance import advance_all_cycles
from app.services.forecast import calculate_available


def _setup_card_and_bill(db):
    """建立信用卡與一筆未繳帳單，回傳 (card, bill)。"""
    card = CreditCard(name="主卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=3,
        due_date=date(2026, 4, 3),
        general_spending=3000000,  # 30,000 元
        is_paid=False,
    )
    db.add(bill)
    db.flush()
    return card, bill


def test_bill_installment_api_create(client, db):
    """POST /obligations 建立帳單分期的 API 整合測試。
    驗證：Installment 欄位正確、原帳單自動標記已繳。
    """
    # 建卡
    resp = client.post("/api/v1/credit-cards", json={
        "name": "主卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    # 建帳單
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03",
        "general_spending": 30000,  # 元
    })
    bill_id = resp.json()["data"]["id"]

    # 建帳單分期（start_date 使用 effective_from_period，由後端計算）
    resp = client.post("/api/v1/obligations", json={
        "name": "3月帳單分期",
        "type": "installment",
        "amount": 5000,  # 每月 5,000 元
        "frequency": "monthly",
        "start_date": "2026-04-15",  # = effective_from_period (next billing cycle)
        "installment": {
            "credit_card_id": card_id,
            "installment_type": "bill",
            "source_bill_id": bill_id,
            "total_amount": 30000,
            "total_periods": 6,
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["installment"]["installment_type"] == "bill"
    assert data["installment"]["source_bill_id"] == bill_id
    assert data["installment"]["effective_from_period"] == "2026-04-15"
    assert data["installment"]["current_period_date"] == "2026-04-15"

    # 驗證原帳單已被標記為已繳
    resp = client.get(f"/api/v1/credit-card-bills?credit_card_id={card_id}")
    bills = resp.json()["data"]
    source_bill = next(b for b in bills if b["id"] == bill_id)
    assert source_bill["is_paid"] is True


def test_bill_installment_appears_in_future_bills(db):
    """帳單分期的 monthly_amount 應出現在未來月份的 installment_amount 聚合中。"""
    card, bill = _setup_card_and_bill(db)
    bill.is_paid = True

    obligation = Obligation(
        name="3月帳單分期", type="installment", amount=500000,
        frequency="monthly", start_date=date(2026, 4, 15),
        next_due_date=date(2026, 4, 15),
    )
    db.add(obligation)
    db.flush()

    db.add(Installment(
        obligation_id=obligation.id,
        credit_card_id=card.id,
        installment_type="bill",
        total_amount=3000000,
        monthly_amount=500000,
        total_periods=6,
        remaining_periods=6,
        current_period_date=date(2026, 4, 15),
        source_bill_id=bill.id,
        effective_from_period=date(2026, 4, 15),
    ))
    db.commit()

    # 4 月帳單的 installment_amount 應包含此分期
    inst_amount = calc_installment_amount(db, card.id, 2026, 4, card.billing_day)
    assert inst_amount == 500000  # 5,000 元 = 500,000 分


def test_bill_installment_not_double_counted_in_forecast(db):
    """原帳單已繳 + 分期透過未來帳單計入 = 不重複扣減。"""
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))  # 100,000 元

    card, bill = _setup_card_and_bill(db)
    bill.is_paid = True  # 原帳單已繳，不再計入 forecast

    obligation = Obligation(
        name="3月帳單分期", type="installment", amount=500000,
        frequency="monthly", start_date=date(2026, 4, 15),
        next_due_date=date(2026, 5, 15),
    )
    db.add(obligation)
    db.flush()

    db.add(Installment(
        obligation_id=obligation.id,
        credit_card_id=card.id,
        installment_type="bill",
        total_amount=3000000,
        monthly_amount=500000,
        total_periods=6,
        remaining_periods=5,
        current_period_date=date(2026, 5, 15),
        source_bill_id=bill.id,
        effective_from_period=date(2026, 4, 15),
    ))

    # 5月帳單（未繳）
    db.add(CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=5,
        due_date=date(2026, 6, 3),
        general_spending=200000,  # 2,000 元一般消費
        installment_amount=500000,
        is_paid=False,
    ))
    db.commit()

    # 查 5/1 ~ 6/30
    result = calculate_available(db, from_date=date(2026, 5, 1), until_date=date(2026, 6, 30))

    # 原帳單（3月）is_paid=True → 不計入
    # 5月帳單 = installment_amount(500000) + general_spending(200000) = 700000
    assert result["period_credit_card_bills"] == 700000
    # type=installment 的 obligation 不計入 period_obligations
    assert result["period_obligations"] == 0


def test_bill_installment_cycle_advance(db):
    """帳單分期經週期推進後，remaining_periods 遞減、current_period_date 更新。"""
    card, bill = _setup_card_and_bill(db)
    bill.is_paid = True

    obligation = Obligation(
        name="帳單分期", type="installment", amount=500000,
        frequency="monthly", start_date=date(2026, 4, 15),
        next_due_date=date(2026, 4, 15),
    )
    db.add(obligation)
    db.flush()

    installment = Installment(
        obligation_id=obligation.id,
        credit_card_id=card.id,
        installment_type="bill",
        total_amount=3000000,
        monthly_amount=500000,
        total_periods=6,
        remaining_periods=6,
        current_period_date=date(2026, 4, 15),
        source_bill_id=bill.id,
        effective_from_period=date(2026, 4, 15),
    )
    db.add(installment)
    db.commit()

    # 推進到 5 月
    advance_all_cycles(db, as_of=date(2026, 5, 1))

    db.refresh(installment)
    db.refresh(obligation)
    assert installment.remaining_periods == 5
    assert obligation.next_due_date == date(2026, 5, 15)
    assert installment.current_period_date == date(2026, 5, 15)


def test_bill_installment_validation_missing_source(client):
    """帳單分期未提供 source_bill_id → 422。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    resp = client.post("/api/v1/obligations", json={
        "name": "Bad",
        "type": "installment",
        "amount": 5000,
        "frequency": "monthly",
        "start_date": "2026-04-15",
        "installment": {
            "credit_card_id": card_id,
            "installment_type": "bill",
            # missing source_bill_id
            "total_amount": 30000,
            "total_periods": 6,
        },
    })
    assert resp.status_code == 422


def test_bill_installment_source_not_found(client):
    """source_bill_id 不存在 → 404。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    resp = client.post("/api/v1/obligations", json={
        "name": "Bad",
        "type": "installment",
        "amount": 5000,
        "frequency": "monthly",
        "start_date": "2026-04-15",
        "installment": {
            "credit_card_id": card_id,
            "installment_type": "bill",
            "source_bill_id": 99999,
            "total_amount": 30000,
            "total_periods": 6,
        },
    })
    assert resp.status_code == 404


def test_bill_installment_source_already_paid(client):
    """已繳帳單不可轉分期 → 400。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    # 建立已繳帳單
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03",
        "general_spending": 30000,
    })
    bill_id = resp.json()["data"]["id"]
    # 標記已繳
    client.put(f"/api/v1/credit-card-bills/{bill_id}", json={"is_paid": True})

    resp = client.post("/api/v1/obligations", json={
        "name": "Bad",
        "type": "installment",
        "amount": 5000,
        "frequency": "monthly",
        "start_date": "2026-04-15",
        "installment": {
            "credit_card_id": card_id,
            "installment_type": "bill",
            "source_bill_id": bill_id,
            "total_amount": 30000,
            "total_periods": 6,
        },
    })
    assert resp.status_code == 400


def test_bill_installment_card_mismatch(client):
    """source_bill 的 credit_card_id 與 installment 的 credit_card_id 不一致 → 400。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "卡A", "billing_day": 15, "due_day": 3,
    })
    card_a_id = resp.json()["data"]["id"]
    resp = client.post("/api/v1/credit-cards", json={
        "name": "卡B", "billing_day": 20, "due_day": 10,
    })
    card_b_id = resp.json()["data"]["id"]

    # 建帳單在卡A
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_a_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03",
        "general_spending": 30000,
    })
    bill_id = resp.json()["data"]["id"]

    # 嘗試用卡B建帳單分期 → 應失敗
    resp = client.post("/api/v1/obligations", json={
        "name": "Bad",
        "type": "installment",
        "amount": 5000,
        "frequency": "monthly",
        "start_date": "2026-04-20",
        "installment": {
            "credit_card_id": card_b_id,
            "installment_type": "bill",
            "source_bill_id": bill_id,
            "total_amount": 30000,
            "total_periods": 6,
        },
    })
    assert resp.status_code == 400
