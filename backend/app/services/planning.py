import calendar
import math
from datetime import date

from sqlalchemy.orm import Session

from app.services.forecast import calculate_available, calculate_timeline
from app.utils.date_helpers import add_months


def evaluate_spend(
    db: Session,
    amount_cents: int,
    as_of: date | None = None,
    until_date: date | None = None,
) -> dict:
    """評估一筆花費是否可行。

    以 calculate_available 計算花費前的可動用金額，
    花費後 = 花費前 - amount_cents，
    is_feasible = 花費後 >= 0。
    """
    today = as_of or date.today()

    if until_date is None:
        # 預設到月底
        last_day = calendar.monthrange(today.year, today.month)[1]
        until_date = date(today.year, today.month, last_day)

    forecast = calculate_available(db, from_date=today, until_date=until_date)

    available_before = forecast["available_amount"]
    available_after = available_before - amount_cents
    is_feasible = available_after >= 0

    if is_feasible:
        summary = f"花費後可動用金額為 {available_after / 100:,.0f} 元，可行"
    else:
        summary = f"花費後可動用金額為 {available_after / 100:,.0f} 元，超支 {abs(available_after) / 100:,.0f} 元"

    return {
        "available_before": available_before,
        "available_after": available_after,
        "period": forecast["period"],
        "is_feasible": is_feasible,
        "summary": summary,
    }


def evaluate_savings_goal(
    db: Session,
    target_amount_cents: int,
    monthly_saving_cents: int | None = None,
    target_date: date | None = None,
    as_of: date | None = None,
) -> dict:
    """評估存錢目標的可行性。

    使用下一個完整月的收支計算每月可存餘裕：
        monthly_surplus = income_total - obligation_total - credit_card_total

    target_date 模式：計算每月需存金額，判斷是否可行。
    monthly_saving 模式：計算需要幾個月，推算達成日。
    """
    today = as_of or date.today()

    # 取 2 個月的 timeline，使用第 2 個月（第一個完整月）的收支數據
    timeline = calculate_timeline(db, months=2, granularity="monthly", as_of=today)

    if len(timeline) >= 2:
        month_data = timeline[1]
    else:
        month_data = timeline[0]

    monthly_surplus = (
        month_data["income_total"]
        - month_data["obligation_total"]
        - month_data["credit_card_total"]
    )

    if target_date:
        # 以日曆月計算月份差
        months_to_target = (target_date.year - today.year) * 12 + (target_date.month - today.month)
        # 若目標日 < 當日日，則不滿一個月，但至少算 1 個月
        if target_date.day < today.day:
            months_to_target = max(1, months_to_target)
        else:
            months_to_target = max(1, months_to_target)

        monthly_needed = math.ceil(target_amount_cents / months_to_target)
        is_feasible = monthly_needed <= monthly_surplus

        if is_feasible:
            summary = f"每月需存 {monthly_needed / 100:,.0f} 元（餘裕 {monthly_surplus / 100:,.0f} 元），可行"
        else:
            summary = f"每月需存 {monthly_needed / 100:,.0f} 元，超過每月餘裕 {monthly_surplus / 100:,.0f} 元"

        return {
            "monthly_surplus": monthly_surplus,
            "monthly_needed": monthly_needed,
            "months_to_target": months_to_target,
            "target_date": target_date.isoformat(),
            "is_feasible": is_feasible,
            "summary": summary,
        }

    elif monthly_saving_cents:
        months_needed = math.ceil(target_amount_cents / monthly_saving_cents)
        projected_date = add_months(today, months_needed)
        is_feasible = monthly_saving_cents <= monthly_surplus

        if is_feasible:
            summary = f"每月存 {monthly_saving_cents / 100:,.0f} 元，需 {months_needed} 個月，預計 {projected_date} 達成"
        else:
            summary = f"每月存 {monthly_saving_cents / 100:,.0f} 元超過餘裕 {monthly_surplus / 100:,.0f} 元"

        return {
            "monthly_surplus": monthly_surplus,
            "monthly_saving": monthly_saving_cents,
            "months_needed": months_needed,
            "projected_date": projected_date.isoformat(),
            "is_feasible": is_feasible,
            "summary": summary,
        }
