import calendar
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.installment import Installment


def calc_first_period_date(start_date: date, billing_day: int) -> date:
    """計算分期的首期扣款日（第一個結帳日 >= start_date）。

    若 start_date 的日期 <= billing_day，首期為同月 billing_day；
    否則為下月 billing_day。
    """
    if start_date.day <= billing_day:
        return date(start_date.year, start_date.month, billing_day)
    # 下個月
    if start_date.month == 12:
        return date(start_date.year + 1, 1, billing_day)
    return date(start_date.year, start_date.month + 1, billing_day)


def calc_billing_period(billing_year: int, billing_month: int, billing_day: int) -> tuple[date, date]:
    """計算帳單的結帳區間：(上一結帳日+1, 本結帳日)。

    例如 billing_day=15, 2026年3月帳單 → (2026-02-16, 2026-03-15)
    """
    bill_date = date(billing_year, billing_month, billing_day)

    # 上一結帳日
    if billing_month == 1:
        prev_bill_date = date(billing_year - 1, 12, billing_day)
    else:
        prev_bill_date = date(billing_year, billing_month - 1, billing_day)

    period_start = date(prev_bill_date.year, prev_bill_date.month, prev_bill_date.day + 1) if prev_bill_date.day < 28 else _next_day(prev_bill_date)
    period_end = bill_date
    return period_start, period_end


def _next_day(d: date) -> date:
    """Return d + 1 day."""
    return date.fromordinal(d.toordinal() + 1)


def calc_installment_amount(db: Session, credit_card_id: int, billing_year: int, billing_month: int, billing_day: int) -> int:
    """即時計算某張卡某月帳單的分期金額（分）。

    條件：Installment.credit_card_id = credit_card_id
          且 Installment.current_period_date 落在結帳區間內
    """
    period_start, period_end = calc_billing_period(billing_year, billing_month, billing_day)

    result = db.query(sa_func.coalesce(sa_func.sum(Installment.monthly_amount), 0)).filter(
        Installment.credit_card_id == credit_card_id,
        Installment.current_period_date >= period_start,
        Installment.current_period_date <= period_end,
        Installment.remaining_periods > 0,
    ).scalar()

    return result


def recalculate_bill_installment_snapshot(db: Session, bill_id: int) -> int:
    """重算單張帳單的 installment_amount snapshot（分）。"""
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    if not bill:
        raise ValueError(f"Bill {bill_id} not found")
    card = db.query(CreditCard).filter(CreditCard.id == bill.credit_card_id).first()
    if not card:
        raise ValueError(f"Card {bill.credit_card_id} not found")
    snapshot = calc_installment_amount(
        db, bill.credit_card_id, bill.billing_year, bill.billing_month, card.billing_day
    )
    bill.installment_amount = snapshot
    return snapshot


def recalculate_card_unpaid_snapshots(db: Session, credit_card_id: int) -> None:
    """重算某張卡所有未繳帳單的 installment_amount snapshot。"""
    unpaid_bills = db.query(CreditCardBill).filter(
        CreditCardBill.credit_card_id == credit_card_id,
        CreditCardBill.is_paid == False,
    ).all()
    for bill in unpaid_bills:
        recalculate_bill_installment_snapshot(db, bill.id)
