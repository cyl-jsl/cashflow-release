from datetime import date

from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.services.forecast import calculate_available


def test_basic_available_amount(db):
    """#1: 帳戶餘額 + 收入 − 固定義務 − budget = 正確可動用金額

    設計文件驗證範例：查詢日 3/14 到月底
    帳戶: 110,000 (80,000 + 30,000)
    薪水 50,000/月 next_date=4/5 → 不在範圍 → 0
    房租 12,000 next_due=4/1 → 不在範圍 → 0
    生活費 budget 8,000/月 → 涵蓋3月 → 扣 8,000
    預期: 110,000 + 0 - 0 - 8,000 = 102,000
    （M0 不含信用卡帳單，故與設計文件的 87,500 不同）
    """
    db.add(Account(name="主要帳戶", type="bank", balance=8000000, currency="TWD"))
    db.add(Account(name="儲蓄帳戶", type="bank", balance=3000000, currency="TWD"))
    db.add(Income(
        name="薪水", amount=5000000, frequency="monthly",
        start_date=date(2026, 1, 5), next_date=date(2026, 4, 5),
    ))
    db.add(Obligation(
        name="房租", type="fixed", amount=1200000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.add(Obligation(
        name="現金生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.commit()

    result = calculate_available(
        db, from_date=date(2026, 3, 14), until_date=date(2026, 3, 31)
    )

    assert result["total_balance"] == 11000000  # 分
    assert result["period_income"] == 0
    assert result["period_obligations"] == 800000  # budget 扣整月
    assert result["available_amount"] == 11000000 + 0 - 800000  # 102,000 元 = 10,200,000 分


def test_budget_deducts_whole_month(db):
    """#3: budget 只要涵蓋某月任何一天即扣整月"""
    db.add(Account(name="A", type="bank", balance=1000000, currency="TWD"))
    db.add(Obligation(
        name="生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.commit()

    # 查詢 3/28~3/31，只涵蓋3月幾天，但仍扣整月
    result = calculate_available(
        db, from_date=date(2026, 3, 28), until_date=date(2026, 3, 31)
    )
    assert result["period_obligations"] == 800000


def test_income_within_range(db):
    """範圍內的收入應被計入"""
    db.add(Account(name="A", type="bank", balance=1000000, currency="TWD"))
    db.add(Income(
        name="薪水", amount=5000000, frequency="monthly",
        start_date=date(2026, 1, 5), next_date=date(2026, 3, 20),
    ))
    db.commit()

    result = calculate_available(
        db, from_date=date(2026, 3, 14), until_date=date(2026, 3, 31)
    )
    assert result["period_income"] == 5000000


def test_installment_type_excluded(db):
    """#2: type=installment 不納入義務加總"""
    db.add(Account(name="A", type="bank", balance=1000000, currency="TWD"))
    db.add(Obligation(
        name="分期", type="installment", amount=250000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 3, 20),
    ))
    db.commit()

    result = calculate_available(
        db, from_date=date(2026, 3, 14), until_date=date(2026, 3, 31)
    )
    assert result["period_obligations"] == 0  # installment 被排除


from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.installment import Installment


def test_forecast_with_credit_card_bills(db):
    """#2 防重複：分期只透過 CreditCardBill 計入，Obligation installment 不重複"""
    db.add(Account(name="主要帳戶", type="bank", balance=11000000, currency="TWD"))  # 110,000 元

    # budget 8,000/月
    db.add(Obligation(
        name="現金生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))

    # 分期義務（不應計入 period_obligations）
    db.add(Obligation(
        name="iPhone 分期", type="installment", amount=250000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))

    # 信用卡
    card = CreditCard(name="主卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    # 分期 Installment (current_period_date in 3月帳單區間 2/16~3/15)
    db.add(Installment(
        obligation_id=2, credit_card_id=card.id, installment_type="purchase",
        total_amount=3000000, monthly_amount=250000, total_periods=12,
        remaining_periods=10, current_period_date=date(2026, 3, 1),
    ))

    # 主卡 3月帳單，due_date 3/25
    db.add(CreditCardBill(
        credit_card_id=card.id, billing_year=2026, billing_month=3,
        due_date=date(2026, 3, 25), general_spending=600000, installment_amount=250000, is_paid=False,
    ))
    db.commit()

    result = calculate_available(db, from_date=date(2026, 3, 14), until_date=date(2026, 3, 31))

    assert result["period_obligations"] == 800000  # budget only, installment excluded
    assert result["period_credit_card_bills"] == 850000  # 250000 inst + 600000 general
    assert result["available_amount"] == 11000000 - 800000 - 850000  # 9,350,000 分 = 93,500 元


def test_paid_bill_not_counted(db):
    """#4: is_paid=true 的帳單不計入"""
    db.add(Account(name="A", type="bank", balance=1000000, currency="TWD"))
    card = CreditCard(name="卡", billing_day=15, due_day=25)
    db.add(card)
    db.flush()
    db.add(CreditCardBill(
        credit_card_id=card.id, billing_year=2026, billing_month=3,
        due_date=date(2026, 3, 25), general_spending=500000, is_paid=True,
    ))
    db.commit()

    result = calculate_available(db, from_date=date(2026, 3, 14), until_date=date(2026, 3, 31))
    assert result["period_credit_card_bills"] == 0


def test_forecast_available_api_default_end_of_month(client):
    """API 端點整合測試：預設到月底"""
    client.post("/api/v1/accounts", json={"name": "A", "type": "bank", "balance": 1000})
    resp = client.get("/api/v1/forecast/available")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_balance"] == 1000.0
    assert "period" in data


def test_available_next_payday_no_monthly_income(client):
    """period_type=next_payday 但無 monthly 收入 → 400 NO_MONTHLY_INCOME"""
    resp = client.get("/api/v1/forecast/available?period_type=next_payday")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "NO_MONTHLY_INCOME"


def test_available_next_payday_success(client):
    """period_type=next_payday 有 monthly 收入 → 使用最早的 next_date"""
    # 建立帳戶和兩筆 monthly 收入，next_date 不同
    client.post("/api/v1/accounts", json={"name": "A", "type": "bank", "balance": 5000})
    client.post("/api/v1/incomes", json={
        "name": "薪水A", "amount": 50000, "frequency": "monthly",
        "start_date": "2026-01-05", "next_date": "2026-04-05",
    })
    client.post("/api/v1/incomes", json={
        "name": "薪水B", "amount": 30000, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-03-20",
    })
    resp = client.get("/api/v1/forecast/available?period_type=next_payday")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # until 應為最早的 next_date 2026-03-20
    assert data["period"]["until"] == "2026-03-20"


def test_available_invalid_days_without_value(client):
    """period_type=days 但未提供 period_value → 400 INVALID_PERIOD"""
    resp = client.get("/api/v1/forecast/available?period_type=days")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "INVALID_PERIOD"
