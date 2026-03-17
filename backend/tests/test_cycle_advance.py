from datetime import date
from app.models.income import Income
from app.models.obligation import Obligation
from app.services.cycle_advance import advance_all_cycles


def test_monthly_advance(db):
    """#6: monthly 推進"""
    income = Income(
        name="薪水", amount=5000000, frequency="monthly",
        start_date=date(2026, 1, 5), next_date=date(2026, 1, 5),
    )
    db.add(income)
    db.commit()

    result = advance_all_cycles(db, as_of=date(2026, 3, 14))
    db.refresh(income)

    assert income.next_date == date(2026, 4, 5)
    assert result["incomes_advanced"] > 0


def test_multi_cycle_advance(db):
    """#7: 長時間未開啟，一次推進多個週期"""
    obligation = Obligation(
        name="房租", type="fixed", amount=1200000, frequency="monthly",
        start_date=date(2025, 6, 1), next_due_date=date(2025, 6, 1),
    )
    db.add(obligation)
    db.commit()

    advance_all_cycles(db, as_of=date(2026, 3, 14))
    db.refresh(obligation)

    # 應推進到 2026-04-01（第一個 > 2026-03-14 的 due date）
    assert obligation.next_due_date == date(2026, 4, 1)


def test_end_date_stops_advance(db):
    """#8: end_date 停止推進"""
    income = Income(
        name="短期兼職", amount=1500000, frequency="monthly",
        start_date=date(2026, 1, 15), end_date=date(2026, 3, 15),
        next_date=date(2026, 1, 15),
    )
    db.add(income)
    db.commit()

    advance_all_cycles(db, as_of=date(2026, 4, 1))
    db.refresh(income)

    # next_date 不應超過 end_date，停在最後一個有效日期
    assert income.next_date <= date(2026, 3, 15)


def test_once_frequency_no_advance(db):
    """once 頻率不推進"""
    obligation = Obligation(
        name="年費", type="fixed", amount=50000, frequency="once",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 1, 1),
    )
    db.add(obligation)
    db.commit()

    advance_all_cycles(db, as_of=date(2026, 6, 1))
    db.refresh(obligation)

    assert obligation.next_due_date == date(2026, 1, 1)


from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.installment import Installment


def test_advance_installment_remaining_periods(db):
    """#9: 推進時遞減 remaining_periods"""
    db.add(Obligation(
        name="分期", type="installment", amount=250000, frequency="monthly",
        start_date=date(2026, 1, 15), next_due_date=date(2026, 3, 15),
    ))
    card = CreditCard(name="卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()
    db.add(Installment(
        obligation_id=1, credit_card_id=card.id, installment_type="purchase",
        total_amount=3000000, monthly_amount=250000, total_periods=12,
        remaining_periods=3, current_period_date=date(2026, 3, 15),
    ))
    db.commit()

    result = advance_all_cycles(db, as_of=date(2026, 3, 20))
    assert result["obligations_advanced"] == 1

    inst = db.query(Installment).first()
    assert inst.remaining_periods == 2
    assert inst.current_period_date == date(2026, 4, 15)


def test_advance_installment_to_zero_ends_obligation(db):
    """#9: remaining_periods 歸零時自動結束父 Obligation"""
    db.add(Obligation(
        name="分期", type="installment", amount=250000, frequency="monthly",
        start_date=date(2026, 1, 15), next_due_date=date(2026, 3, 15),
    ))
    card = CreditCard(name="卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()
    db.add(Installment(
        obligation_id=1, credit_card_id=card.id, installment_type="purchase",
        total_amount=3000000, monthly_amount=250000, total_periods=12,
        remaining_periods=1, current_period_date=date(2026, 3, 15),
    ))
    db.commit()

    advance_all_cycles(db, as_of=date(2026, 3, 20))

    inst = db.query(Installment).first()
    assert inst.remaining_periods == 0

    ob = db.query(Obligation).first()
    assert ob.end_date is not None  # 已標記結束


def test_advance_does_not_change_bill_snapshot(db):
    """advance-cycles 推進 current_period_date 後，帳單 installment_amount 不變。"""
    card = CreditCard(name="卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    bill = CreditCardBill(
        credit_card_id=card.id,
        billing_year=2026, billing_month=3,
        due_date=date(2026, 4, 3),
        general_spending=600000,
        is_paid=False,
        installment_amount=250000,
    )
    db.add(bill)

    ob = Obligation(
        name="分期", type="installment", amount=250000, frequency="monthly",
        start_date=date(2026, 1, 15), next_due_date=date(2026, 3, 15),
    )
    db.add(ob)
    db.flush()

    db.add(Installment(
        obligation_id=ob.id, credit_card_id=card.id, installment_type="purchase",
        total_amount=3000000, monthly_amount=250000, total_periods=12,
        remaining_periods=10, current_period_date=date(2026, 3, 15),
    ))
    db.commit()

    advance_all_cycles(db, as_of=date(2026, 3, 20))

    db.refresh(bill)
    assert bill.installment_amount == 250000  # snapshot 不變
