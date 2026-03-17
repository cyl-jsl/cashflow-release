import calendar
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import (
    DashboardSummary, UpcomingDue, StaleAccount, AccountSummary,
)
from app.services.forecast import calculate_available

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

STALE_DAYS = 7
UPCOMING_DAYS = 7


@router.get("/summary", response_model=SuccessResponse[DashboardSummary])
def get_dashboard_summary(db: Session = Depends(get_db)):
    today = date.today()
    now = datetime.now()

    # 1. 可動用金額（到發薪日）
    monthly_incomes = db.query(Income).filter(Income.frequency == "monthly").all()
    if monthly_incomes:
        until_date = min(i.next_date for i in monthly_incomes)
    else:
        last_day = calendar.monthrange(today.year, today.month)[1]
        until_date = date(today.year, today.month, last_day)

    forecast = calculate_available(db, from_date=today, until_date=until_date)

    # 2. 帳戶摘要
    accounts = db.query(Account).all()
    account_summaries = []
    stale_accounts = []
    for a in accounts:
        days_since = (now - a.balance_updated_at).days
        is_stale = days_since >= STALE_DAYS
        account_summaries.append(AccountSummary(
            id=a.id,
            name=a.name,
            balance=a.balance / 100,
            balance_updated_at=a.balance_updated_at,
            is_stale=is_stale,
        ))
        if is_stale:
            stale_accounts.append(StaleAccount(
                id=a.id, name=a.name, days_since_update=days_since,
            ))

    # 3. 近期到期（7 天內）
    upcoming_end = today + timedelta(days=UPCOMING_DAYS)
    upcoming_dues: list[UpcomingDue] = []

    # 義務（fixed + budget）
    obligations = db.query(Obligation).filter(
        Obligation.type != "installment",
        Obligation.next_due_date >= today,
        Obligation.next_due_date <= upcoming_end,
    ).all()
    for ob in obligations:
        upcoming_dues.append(UpcomingDue(
            type="obligation",
            name=ob.name,
            amount=ob.amount / 100,
            due_date=ob.next_due_date,
        ))

    # 信用卡帳單
    bills = db.query(CreditCardBill).filter(
        CreditCardBill.due_date >= today,
        CreditCardBill.due_date <= upcoming_end,
    ).all()
    for bill in bills:
        card = db.query(CreditCard).filter(CreditCard.id == bill.credit_card_id).first()
        inst_amount = bill.installment_amount or 0
        total = (inst_amount + bill.general_spending + bill.carried_forward) / 100
        upcoming_dues.append(UpcomingDue(
            type="credit_card_bill",
            name=f"{card.name} {bill.billing_month}月帳單",
            amount=total,
            due_date=bill.due_date,
            is_paid=bill.is_paid,
        ))

    # 按 due_date 排序
    upcoming_dues.sort(key=lambda x: x.due_date)

    return SuccessResponse.of(DashboardSummary(
        total_balance=forecast["total_balance"] / 100,
        available_amount=forecast["available_amount"] / 100,
        available_period=forecast["period"],
        accounts=account_summaries,
        upcoming_dues=upcoming_dues,
        stale_accounts=stale_accounts,
    ))
