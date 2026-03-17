"""循環利息計算與結轉服務。

設計：部分繳款時，未繳本金 + 利息一起結轉至下期帳單的 carried_forward 欄位。
利息計算採簡化月利率 = 年利率 / 12（V2 可改進為精確日計息）。
"""
from datetime import date

from sqlalchemy.orm import Session

from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill


def calculate_and_carry_forward(
    db: Session,
    bill_id: int,
    paid_amount_cents: int,
) -> dict:
    """計算部分繳款的結轉金額（本金 + 利息）並寫入下期帳單。

    Returns:
        {
            "unpaid_cents": int,            # 未繳本金（分）
            "interest_cents": int,          # 產生的利息（分）
            "carried_forward_cents": int,   # 結轉至下期的總額（本金 + 利息）
            "next_bill_id": int|None,       # 下期帳單 ID（若有建立/更新）
        }
    """
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    if not bill:
        raise ValueError("帳單不存在")

    card = db.query(CreditCard).filter(CreditCard.id == bill.credit_card_id).first()
    if not card:
        raise ValueError("信用卡不存在")

    # 計算帳單總額（含分期 + 一般消費 + 前期結轉）
    inst_amount = bill.installment_amount or 0
    total_cents = inst_amount + bill.general_spending + bill.carried_forward

    # 計算未繳金額
    unpaid_cents = max(0, total_cents - paid_amount_cents)

    if unpaid_cents == 0:
        return {"unpaid_cents": 0, "interest_cents": 0, "carried_forward_cents": 0, "next_bill_id": None}

    # 計算利息
    rate = float(card.revolving_interest_rate) if card.revolving_interest_rate is not None else 0
    monthly_rate = rate / 12 if rate > 0 else 0
    interest_cents = round(unpaid_cents * monthly_rate)

    # 結轉金額 = 未繳本金 + 利息
    carried_forward_cents = unpaid_cents + interest_cents

    # 找或建下期帳單
    next_year, next_month = _next_billing_period(bill.billing_year, bill.billing_month)
    next_due = _calc_due_date(next_year, next_month, card.due_day, card.billing_day)

    next_bill = db.query(CreditCardBill).filter(
        CreditCardBill.credit_card_id == card.id,
        CreditCardBill.billing_year == next_year,
        CreditCardBill.billing_month == next_month,
    ).first()

    if next_bill:
        next_bill.carried_forward = carried_forward_cents
    else:
        next_bill = CreditCardBill(
            credit_card_id=card.id,
            billing_year=next_year,
            billing_month=next_month,
            due_date=next_due,
            general_spending=0,
            carried_forward=carried_forward_cents,
        )
        db.add(next_bill)

    db.flush()
    db.refresh(next_bill)

    from app.services.credit_card_bill import recalculate_bill_installment_snapshot
    recalculate_bill_installment_snapshot(db, next_bill.id)
    db.flush()

    return {
        "unpaid_cents": unpaid_cents,
        "interest_cents": interest_cents,
        "carried_forward_cents": carried_forward_cents,
        "next_bill_id": next_bill.id,
    }


def _next_billing_period(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _calc_due_date(year: int, month: int, due_day: int, billing_day: int) -> date:
    """計算繳款截止日。若 due_day < billing_day 代表跨月繳款。"""
    if due_day < billing_day:
        if month == 12:
            return date(year + 1, 1, due_day)
        return date(year, month + 1, due_day)
    return date(year, month, due_day)
