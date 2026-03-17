import calendar
from datetime import date

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.income import Income
from app.models.installment import Installment
from app.models.obligation import Obligation
from app.utils.date_helpers import advance_date


def calculate_available(
    db: Session,
    from_date: date,
    until_date: date,
) -> dict:
    """計算可動用金額。含信用卡帳單。"""
    # 1. 帳戶餘額加總
    accounts = db.query(Account).all()
    total_balance = sum(a.balance for a in accounts)

    # 2. 展開範圍內的 Income
    period_income = _sum_periodic_events_in_range(
        db.query(Income).all(), "next_date", from_date, until_date
    )

    # 3. 展開範圍內的 Obligation（排除 installment）
    obligations = db.query(Obligation).filter(Obligation.type != "installment").all()
    period_obligations = 0
    for ob in obligations:
        if ob.type == "budget":
            # budget 涵蓋到的月份各扣一個月
            period_obligations += _budget_amount_in_range(ob, from_date, until_date)
        else:
            # fixed: 展開週期性事件
            period_obligations += _sum_single_periodic(ob, "next_due_date", from_date, until_date)

    # 4. 信用卡帳單：未繳且 due_date 在範圍內
    bills = db.query(CreditCardBill).filter(
        CreditCardBill.is_paid == False,
        CreditCardBill.due_date >= from_date,
        CreditCardBill.due_date <= until_date,
    ).all()

    period_credit_card_bills = 0
    for bill in bills:
        inst_amount = bill.installment_amount or 0
        period_credit_card_bills += inst_amount + bill.general_spending + bill.carried_forward

    available_amount = total_balance + period_income - period_obligations - period_credit_card_bills

    return {
        "total_balance": total_balance,
        "period_income": period_income,
        "period_obligations": period_obligations,
        "period_credit_card_bills": period_credit_card_bills,
        "available_amount": available_amount,
        "period": {"from": from_date.isoformat(), "until": until_date.isoformat()},
    }


def _sum_periodic_events_in_range(
    records: list, date_field: str, from_date: date, until_date: date
) -> int:
    """加總所有記錄在範圍內的週期性金額。"""
    total = 0
    for record in records:
        total += _sum_single_periodic(record, date_field, from_date, until_date)
    return total


def _sum_single_periodic(record, date_field: str, from_date: date, until_date: date) -> int:
    """展開單筆記錄的週期，加總落在 [from_date, until_date] 內的金額。"""
    total = 0
    current = getattr(record, date_field)

    # 最多展開 120 期作為安全上限
    for _ in range(120):
        if current > until_date:
            break
        # 檢查 end_date
        if record.end_date and current > record.end_date:
            break
        if current >= from_date:
            total += record.amount
        # 推進到下一期
        next_val = advance_date(current, record.frequency)
        if next_val is None:
            break
        current = next_val

    return total


def _budget_amount_in_range(obligation, from_date: date, until_date: date) -> int:
    """budget 涵蓋到的月份各扣一個月。涵蓋某月任何一天即扣整月。"""
    months = set()
    d = from_date
    while d <= until_date:
        months.add((d.year, d.month))
        # 跳到下個月1號
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)

    return obligation.amount * len(months)


def calculate_timeline(
    db: Session,
    months: int,
    granularity: str,
    as_of: date | None = None,
) -> list[dict]:
    """產生未來 N 個月的餘額走勢時間序列。

    每個時間點 = 前一點餘額 + 該期收入 − 該期義務(不含 installment) − 該期信用卡帳單。
    對已建立的帳單使用 installment_amount + general_spending；
    對尚未建立帳單的未來月份，僅以 Installment 表聚合已知分期金額（不預估 general_spending）。
    granularity 目前僅支援 monthly。
    """
    today = as_of or date.today()
    timeline = []

    # 起始餘額 = 所有帳戶餘額加總
    accounts = db.query(Account).all()
    running_balance = sum(a.balance for a in accounts)

    # 預先查詢，避免迴圈內重複查詢（N+1）
    incomes = db.query(Income).all()
    obligations = db.query(Obligation).filter(Obligation.type != "installment").all()
    cards = {c.id: c for c in db.query(CreditCard).all()}

    for i in range(months):
        # 計算當月區間
        if i == 0:
            period_start = today
        else:
            prev_end = timeline[i - 1]["_raw_end"]
            if prev_end.month == 12:
                period_start = date(prev_end.year + 1, 1, 1)
            else:
                period_start = date(prev_end.year, prev_end.month + 1, 1)

        # 月末
        if i == 0:
            last_day = calendar.monthrange(today.year, today.month)[1]
            period_end = date(today.year, today.month, last_day)
        else:
            last_day = calendar.monthrange(period_start.year, period_start.month)[1]
            period_end = date(period_start.year, period_start.month, last_day)

        # 計算該期間的收入（使用既有 helper）
        period_income = _sum_periodic_events_in_range(incomes, "next_date", period_start, period_end)

        # 計算該期間的義務（排除 installment，使用既有 helper）
        period_obligations = 0
        for ob in obligations:
            if ob.type == "budget":
                period_obligations += _budget_amount_in_range(ob, period_start, period_end)
            else:
                period_obligations += _sum_single_periodic(ob, "next_due_date", period_start, period_end)

        # 計算該期間的信用卡支出
        bills = db.query(CreditCardBill).filter(
            CreditCardBill.is_paid == False,
            CreditCardBill.due_date >= period_start,
            CreditCardBill.due_date <= period_end,
        ).all()

        period_credit_card = 0
        billed_card_months = set()
        for bill in bills:
            inst_amount = bill.installment_amount or 0
            period_credit_card += inst_amount + bill.general_spending + bill.carried_forward
            billed_card_months.add((bill.credit_card_id, bill.billing_year, bill.billing_month))

        # 未建立帳單的未來月份：聚合已知分期
        future_installments = db.query(Installment).filter(
            Installment.remaining_periods > 0,
            Installment.current_period_date >= period_start,
            Installment.current_period_date <= period_end,
        ).all()
        for inst in future_installments:
            card = cards.get(inst.credit_card_id)
            if card:
                bill_month = inst.current_period_date.month
                bill_year = inst.current_period_date.year
                if (inst.credit_card_id, bill_year, bill_month) not in billed_card_months:
                    period_credit_card += inst.monthly_amount

        running_balance = running_balance + period_income - period_obligations - period_credit_card

        has_future_note = i > 0

        point = {
            "date": period_end.isoformat(),
            "balance": running_balance,
            "income_total": period_income,
            "obligation_total": period_obligations,
            "credit_card_total": period_credit_card,
            "note": "不含未來一般消費預估" if has_future_note else None,
            "_raw_end": period_end,
        }
        timeline.append(point)

    for point in timeline:
        del point["_raw_end"]

    return timeline


def calculate_simulated_timeline(
    db: Session,
    monthly_income_change_cents: int,
    monthly_expense_change_cents: int,
    months: int,
    as_of: date | None = None,
) -> dict:
    """情境模擬：在現有 timeline 基礎上疊加收支增減。

    返回 baseline（原始）和 simulated（調整後）兩組 timeline 供對照。
    增減以「分」為單位，每月累積。
    """
    baseline = calculate_timeline(db, months=months, granularity="monthly", as_of=as_of)

    simulated = []
    cumulative_delta = 0
    monthly_delta = monthly_income_change_cents - monthly_expense_change_cents

    for point in baseline:
        cumulative_delta += monthly_delta
        sim_point = {
            "date": point["date"],
            "balance": point["balance"] + cumulative_delta,
            "income_total": point["income_total"] + monthly_income_change_cents,
            "obligation_total": point["obligation_total"] + monthly_expense_change_cents,
            "credit_card_total": point["credit_card_total"],
            "note": point.get("note"),
        }
        simulated.append(sim_point)

    return {
        "baseline": baseline,
        "simulated": simulated,
    }
