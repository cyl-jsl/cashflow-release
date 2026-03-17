from datetime import date

from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.installment import Installment
from app.models.obligation import Obligation
from app.services.credit_card_bill import (
    recalculate_bill_installment_snapshot,
    recalculate_card_unpaid_snapshots,
)


def _setup(db):
    """建立信用卡、帳單、分期的基礎資料。"""
    card = CreditCard(name="測試卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=3,
        due_date=date(2026, 4, 3),
        general_spending=600000,
        is_paid=False,
    )
    db.add(bill)
    db.flush()

    obligation = Obligation(
        name="iPhone 分期", type="installment", amount=250000,
        frequency="monthly", start_date=date(2026, 3, 1),
        next_due_date=date(2026, 3, 1),
    )
    db.add(obligation)
    db.flush()

    installment = Installment(
        obligation_id=obligation.id,
        credit_card_id=card.id,
        installment_type="purchase",
        total_amount=3000000,
        monthly_amount=250000,
        total_periods=12,
        remaining_periods=12,
        current_period_date=date(2026, 3, 1),
    )
    db.add(installment)
    db.flush()

    return card, bill, obligation, installment


def test_recalculate_bill_installment_snapshot(db):
    """recalculate_bill_installment_snapshot 應正確計算並存入 installment_amount。"""
    card, bill, _, _ = _setup(db)

    assert bill.installment_amount is None  # 初始為 None

    result = recalculate_bill_installment_snapshot(db, bill.id)

    assert result == 250000  # 分
    assert bill.installment_amount == 250000


def test_recalculate_card_unpaid_snapshots(db):
    """recalculate_card_unpaid_snapshots 只更新未繳帳單。"""
    card, bill, _, _ = _setup(db)

    # 新增一筆已繳帳單
    paid_bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=2,
        due_date=date(2026, 3, 3),
        general_spending=400000,
        is_paid=True,
    )
    db.add(paid_bill)
    db.flush()

    recalculate_card_unpaid_snapshots(db, card.id)

    assert bill.installment_amount == 250000  # 未繳帳單已更新
    assert paid_bill.installment_amount is None  # 已繳帳單未動


def test_snapshot_set_on_bill_creation(client, db):
    """POST /credit-card-bills 建立帳單後，snapshot 自動計算。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "測試卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    # 先建分期
    client.post("/api/v1/obligations", json={
        "name": "iPhone", "type": "installment", "amount": 2500,
        "frequency": "monthly", "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })

    # 建帳單
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 6000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["installment_amount"] == 2500.0

    # 驗證 DB 中的存儲值
    from app.models.credit_card_bill import CreditCardBill
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == data["id"]).first()
    assert bill.installment_amount == 250000


def test_snapshot_updated_on_installment_create(client, db):
    """建立分期後，既有帳單的 snapshot 自動更新。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "測試卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    # 先建帳單（此時無分期，snapshot = 0）
    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 6000,
    })
    bill_id = resp.json()["data"]["id"]
    from app.models.credit_card_bill import CreditCardBill
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    assert bill.installment_amount == 0

    # 建分期 → 應觸發帳單 snapshot 更新
    client.post("/api/v1/obligations", json={
        "name": "iPhone", "type": "installment", "amount": 2500,
        "frequency": "monthly", "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })

    db.refresh(bill)
    assert bill.installment_amount == 250000


def test_snapshot_updated_on_installment_delete(client, db):
    """刪除分期後，帳單 snapshot 更新。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "測試卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 6000,
    })
    bill_id = resp.json()["data"]["id"]

    resp = client.post("/api/v1/obligations", json={
        "name": "iPhone", "type": "installment", "amount": 2500,
        "frequency": "monthly", "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })
    ob_id = resp.json()["data"]["id"]

    from app.models.credit_card_bill import CreditCardBill
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    assert bill.installment_amount == 250000

    resp = client.delete(f"/api/v1/obligations/{ob_id}")
    assert resp.status_code == 200

    db.refresh(bill)
    assert bill.installment_amount == 0


def test_snapshot_updated_on_obligation_amount_change(client, db):
    """更新分期義務金額後，帳單 snapshot 自動更新。"""
    resp = client.post("/api/v1/credit-cards", json={
        "name": "測試卡", "billing_day": 15, "due_day": 3,
    })
    card_id = resp.json()["data"]["id"]

    resp = client.post("/api/v1/credit-card-bills", json={
        "credit_card_id": card_id,
        "billing_year": 2026, "billing_month": 3,
        "due_date": "2026-04-03", "general_spending": 6000,
    })
    bill_id = resp.json()["data"]["id"]

    resp = client.post("/api/v1/obligations", json={
        "name": "iPhone", "type": "installment", "amount": 2500,
        "frequency": "monthly", "start_date": "2026-03-01",
        "installment": {"credit_card_id": card_id, "total_amount": 30000, "total_periods": 12},
    })
    ob_id = resp.json()["data"]["id"]

    from app.models.credit_card_bill import CreditCardBill
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    assert bill.installment_amount == 250000

    resp = client.put(f"/api/v1/obligations/{ob_id}", json={"amount": 3000})
    assert resp.status_code == 200

    db.refresh(bill)
    assert bill.installment_amount == 300000


def test_snapshot_on_carry_forward_new_bill(db):
    """部分繳款結轉建立新帳單時，新帳單的 snapshot 正確。"""
    from app.models.credit_card import CreditCard
    from app.models.obligation import Obligation
    from app.models.installment import Installment

    card = CreditCard(name="測試卡", billing_day=15, due_day=3, revolving_interest_rate=0.15)
    db.add(card)
    db.flush()

    obligation = Obligation(
        name="分期", type="installment", amount=250000,
        frequency="monthly", start_date=date(2026, 3, 1),
        next_due_date=date(2026, 4, 1),
    )
    db.add(obligation)
    db.flush()

    installment = Installment(
        obligation_id=obligation.id,
        credit_card_id=card.id,
        installment_type="purchase",
        total_amount=3000000,
        monthly_amount=250000,
        total_periods=12,
        remaining_periods=11,
        current_period_date=date(2026, 4, 15),
    )
    db.add(installment)
    db.flush()

    bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=3,
        due_date=date(2026, 4, 3),
        general_spending=1000000,
        installment_amount=250000,
    )
    db.add(bill)
    db.commit()

    from app.services.revolving_interest import calculate_and_carry_forward
    result = calculate_and_carry_forward(db, bill_id=bill.id, paid_amount_cents=600000)

    next_bill = db.query(CreditCardBill).filter(CreditCardBill.id == result["next_bill_id"]).first()
    assert next_bill.installment_amount == 250000


def test_snapshot_persists_after_advance_cycles(db):
    """advance-cycles 推進 current_period_date 後，帳單 snapshot 不變。"""
    from app.services.cycle_advance import advance_all_cycles
    from app.services.credit_card_bill import recalculate_bill_installment_snapshot

    card, bill, obligation, installment = _setup(db)

    recalculate_bill_installment_snapshot(db, bill.id)
    db.commit()

    assert bill.installment_amount == 250000

    advance_all_cycles(db, as_of=date(2026, 3, 20))

    db.refresh(bill)
    db.refresh(installment)

    assert installment.current_period_date == date(2026, 4, 1)
    assert bill.installment_amount == 250000  # snapshot 不變


def test_snapshot_null_treated_as_zero(db):
    """installment_amount 為 NULL 時，讀取視為 0。"""
    from app.models.credit_card import CreditCard

    card = CreditCard(name="測試卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=3,
        due_date=date(2026, 4, 3),
        general_spending=600000,
        is_paid=True,
    )
    db.add(bill)
    db.commit()

    assert bill.installment_amount is None

    from app.routers.credit_card_bills import _to_read
    read = _to_read(bill)
    assert read.installment_amount == 0.0
    assert read.total_amount == 6000.0


def test_paid_bills_not_recalculated(db):
    """已繳帳單的 snapshot 不被 recalculate_card_unpaid_snapshots 影響。"""
    from app.models.credit_card import CreditCard
    from app.services.credit_card_bill import recalculate_card_unpaid_snapshots

    card = CreditCard(name="測試卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    paid_bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=2,
        due_date=date(2026, 3, 3),
        general_spending=400000,
        is_paid=True,
        installment_amount=100000,
    )
    db.add(paid_bill)
    db.flush()

    recalculate_card_unpaid_snapshots(db, card.id)

    db.refresh(paid_bill)
    assert paid_bill.installment_amount == 100000  # 不變
