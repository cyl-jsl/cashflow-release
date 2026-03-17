from datetime import date

from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.services.forecast import calculate_timeline


def test_timeline_basic_monthly(db):
    """月粒度：每月餘額 = 前月 + 收入 - 義務"""
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    db.add(Income(
        name="薪水", amount=5000000, frequency="monthly",
        start_date=date(2026, 1, 5), next_date=date(2026, 4, 5),
    ))
    db.add(Obligation(
        name="房租", type="fixed", amount=1200000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.add(Obligation(
        name="生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.commit()

    result = calculate_timeline(db, months=3, granularity="monthly", as_of=date(2026, 3, 14))

    assert len(result) == 3
    # 第一個月（3月）：到 3/31
    assert result[0]["date"] == date(2026, 3, 31).isoformat()
    # 帳戶 10,000,000 + 收入 0（3月已無薪水 next_date=4/5）- 房租 0 (next_due=4/1) - budget 800,000
    assert result[0]["balance"] == 10000000 - 800000

    # 第二個月（4月）：前月餘額 + 4月收入 - 4月支出
    # 前月餘額 9,200,000 + 薪水 5,000,000 - 房租 1,200,000 - budget 800,000
    assert result[1]["balance"] == 9200000 + 5000000 - 1200000 - 800000


def test_timeline_with_credit_card_bills(db):
    """timeline 含未繳信用卡帳單"""
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    card = CreditCard(name="主卡", billing_day=15, due_day=3)
    db.add(card)
    db.commit()
    db.refresh(card)

    db.add(CreditCardBill(
        credit_card_id=card.id, billing_year=2026, billing_month=3,
        due_date=date(2026, 4, 3), general_spending=600000, is_paid=False,
    ))
    db.commit()

    result = calculate_timeline(db, months=2, granularity="monthly", as_of=date(2026, 3, 14))

    # 4月有信用卡帳單到期
    assert result[1]["credit_card_total"] == 600000


def test_timeline_future_months_no_general_spending(db):
    """未來月份信用卡只含已知分期，不含 general_spending"""
    db.add(Account(name="銀行", type="bank", balance=5000000, currency="TWD"))
    db.commit()

    # 沒有帳單 → credit_card_total 為 0
    result = calculate_timeline(db, months=2, granularity="monthly", as_of=date(2026, 3, 14))
    assert result[0]["credit_card_total"] == 0
    assert result[1]["credit_card_total"] == 0


def test_timeline_returns_correct_length(db):
    """timeline 回傳正確的月數"""
    db.add(Account(name="銀行", type="bank", balance=1000000, currency="TWD"))
    db.commit()

    result = calculate_timeline(db, months=6, granularity="monthly", as_of=date(2026, 3, 14))
    assert len(result) == 6


def test_timeline_endpoint_default(client, db):
    """GET /forecast/timeline 預設 6 個月、monthly"""
    from app.models.account import Account
    db.add(Account(name="銀行", type="bank", balance=5000000, currency="TWD"))
    db.commit()

    resp = client.get("/api/v1/forecast/timeline")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["granularity"] == "monthly"
    assert data["months"] == 6
    assert len(data["timeline"]) == 6
    # 金額應為元（除以 100）
    assert data["timeline"][0]["balance"] == 50000.0


def test_timeline_endpoint_custom_months(client, db):
    """GET /forecast/timeline?months=3"""
    from app.models.account import Account
    db.add(Account(name="銀行", type="bank", balance=1000000, currency="TWD"))
    db.commit()

    resp = client.get("/api/v1/forecast/timeline?months=3")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["months"] == 3
    assert len(data["timeline"]) == 3
