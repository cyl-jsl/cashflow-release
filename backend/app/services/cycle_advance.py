from datetime import date

from sqlalchemy.orm import Session

from app.models.income import Income
from app.models.installment import Installment
from app.models.obligation import Obligation
from app.utils.date_helpers import advance_date


def advance_all_cycles(db: Session, as_of: date | None = None) -> dict:
    """推進所有過期的 Income/Obligation 週期至 as_of 之後。"""
    if as_of is None:
        as_of = date.today()

    incomes_advanced = 0
    obligations_advanced = 0

    # 推進 Income
    incomes = db.query(Income).filter(Income.next_date <= as_of).all()
    for income in incomes:
        count = _advance_record(income, "next_date", as_of)
        incomes_advanced += count

    # 推進 Obligation（含 installment）
    obligations = db.query(Obligation).filter(Obligation.next_due_date <= as_of).all()
    for obligation in obligations:
        count = _advance_record(obligation, "next_due_date", as_of)
        obligations_advanced += count

        # 分期付款額外處理
        if obligation.type == "installment" and count > 0:
            installment = db.query(Installment).filter(
                Installment.obligation_id == obligation.id
            ).first()
            if installment:
                _advance_installment(installment, count, obligation)

    db.commit()
    return {
        "incomes_advanced": incomes_advanced,
        "obligations_advanced": obligations_advanced,
    }


def _advance_record(record, date_field: str, as_of: date) -> int:
    """推進單筆記錄直到日期超過 as_of，回傳推進次數。"""
    count = 0
    current = getattr(record, date_field)

    while current <= as_of:
        next_val = advance_date(current, record.frequency)
        if next_val is None:
            # once 頻率，不推進
            break
        # 若有 end_date 且推進後超過，停止
        end = record.end_date
        if end and next_val > end:
            break
        current = next_val
        count += 1

    setattr(record, date_field, current)
    return count


def _advance_installment(installment, advance_count: int, obligation) -> None:
    """推進分期：遞減 remaining_periods，更新 current_period_date，歸零時結束父 Obligation。"""
    installment.remaining_periods = max(0, installment.remaining_periods - advance_count)
    # 更新 current_period_date 至與 obligation.next_due_date 同步
    installment.current_period_date = obligation.next_due_date

    if installment.remaining_periods == 0:
        # 自動標記父 Obligation 結束
        obligation.end_date = obligation.next_due_date
