from datetime import date
from app.utils.date_helpers import advance_date


def test_monthly_normal():
    assert advance_date(date(2026, 3, 15), "monthly") == date(2026, 4, 15)


def test_monthly_end_of_month():
    """1/31 → 2/28（非閏年）"""
    assert advance_date(date(2026, 1, 31), "monthly") == date(2026, 2, 28)


def test_monthly_march_31():
    """3/31 → 4/30"""
    assert advance_date(date(2026, 3, 31), "monthly") == date(2026, 4, 30)


def test_biweekly():
    assert advance_date(date(2026, 3, 1), "biweekly") == date(2026, 3, 15)


def test_quarterly():
    assert advance_date(date(2026, 1, 15), "quarterly") == date(2026, 4, 15)


def test_quarterly_end_of_month():
    """1/31 → 4/30"""
    assert advance_date(date(2026, 1, 31), "quarterly") == date(2026, 4, 30)


def test_yearly():
    assert advance_date(date(2026, 3, 14), "yearly") == date(2027, 3, 14)


def test_yearly_leap_day():
    """2/29（閏年）→ 2/28（非閏年）"""
    assert advance_date(date(2024, 2, 29), "yearly") == date(2025, 2, 28)


def test_yearly_december():
    """12月 + 12個月 = 次年12月"""
    assert advance_date(date(2026, 12, 15), "yearly") == date(2027, 12, 15)


def test_once_returns_none():
    assert advance_date(date(2026, 3, 14), "once") is None
