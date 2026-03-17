import calendar
from datetime import date, timedelta


def advance_date(current: date, frequency: str) -> date | None:
    """根據頻率推進日期。once 回傳 None（不推進）。"""
    if frequency == "once":
        return None
    if frequency == "biweekly":
        return current + timedelta(days=14)
    if frequency == "monthly":
        return add_months(current, 1)
    if frequency == "quarterly":
        return add_months(current, 3)
    if frequency == "yearly":
        return add_months(current, 12)
    raise ValueError(f"Unknown frequency: {frequency}")


def add_months(d: date, months: int) -> date:
    """加 N 個月，若目標月無該日則取月末。"""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(d.day, max_day)
    return date(year, month, day)
