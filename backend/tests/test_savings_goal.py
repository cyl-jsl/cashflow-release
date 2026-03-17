import math
from datetime import date

from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.models.income import Income
from app.models.installment import Installment
from app.models.obligation import Obligation
from app.services.planning import evaluate_savings_goal


def _setup_basic_scenario(db):
    """月收入 50,000 元、固定支出 20,000 元、生活費 8,000 元。"""
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))  # 100,000 元
    db.add(Income(
        name="薪水", amount=5000000, frequency="monthly",
        start_date=date(2026, 1, 5), next_date=date(2026, 4, 5),
    ))
    db.add(Obligation(
        name="房租", type="fixed", amount=2000000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.add(Obligation(
        name="生活費", type="budget", amount=800000, frequency="monthly",
        start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1),
    ))
    db.commit()


def test_savings_goal_with_target_date(db):
    """提供 target_date → 算每月需存金額 + 可行性。"""
    _setup_basic_scenario(db)

    result = evaluate_savings_goal(
        db,
        target_amount_cents=12000000,  # 120,000 元
        target_date=date(2026, 9, 15),  # ~6 個月
        as_of=date(2026, 3, 15),
    )

    assert result["months_to_target"] == 6
    assert result["monthly_needed"] == 2000000  # 120,000 / 6 = 20,000 = 2,000,000 分
    # 月餘裕 = 50,000 - 20,000 - 8,000 = 22,000 元 = 2,200,000 分
    assert result["monthly_surplus"] == 2200000
    assert result["is_feasible"] is True  # 20,000 <= 22,000


def test_savings_goal_with_monthly_saving(db):
    """提供 monthly_saving → 算達成日期。"""
    _setup_basic_scenario(db)

    result = evaluate_savings_goal(
        db,
        target_amount_cents=12000000,  # 120,000 元
        monthly_saving_cents=2000000,   # 每月存 20,000 元
        as_of=date(2026, 3, 15),
    )

    assert result["months_needed"] == 6  # 120,000 / 20,000 = 6
    assert result["monthly_surplus"] == 2200000
    assert result["is_feasible"] is True  # 20,000 <= 22,000
    assert "projected_date" in result


def test_savings_goal_infeasible(db):
    """每月需存金額超過餘裕 → is_feasible=False。"""
    _setup_basic_scenario(db)

    result = evaluate_savings_goal(
        db,
        target_amount_cents=12000000,  # 120,000 元
        target_date=date(2026, 4, 15),  # 1 個月
        as_of=date(2026, 3, 15),
    )

    # 需一個月存 120,000 元，超過每月餘裕 22,000
    assert result["is_feasible"] is False
    assert result["monthly_needed"] == 12000000


def test_savings_goal_with_credit_card_bills(db):
    """信用卡帳單應降低 monthly_surplus。"""
    _setup_basic_scenario(db)

    # 加信用卡和分期
    card = CreditCard(name="主卡", billing_day=15, due_day=3)
    db.add(card)
    db.flush()

    # 分期義務（不計入 period_obligations）
    ob = Obligation(
        name="iPhone 分期", type="installment", amount=250000,
        frequency="monthly", start_date=date(2026, 1, 1),
        next_due_date=date(2026, 5, 1),
    )
    db.add(ob)
    db.flush()

    db.add(Installment(
        obligation_id=ob.id, credit_card_id=card.id, installment_type="purchase",
        total_amount=3000000, monthly_amount=250000, total_periods=12,
        remaining_periods=8, current_period_date=date(2026, 4, 15),
    ))
    db.commit()

    result = evaluate_savings_goal(
        db,
        target_amount_cents=12000000,
        target_date=date(2026, 9, 15),
        as_of=date(2026, 3, 15),
    )

    # 月餘裕應低於無信用卡場景的 2,200,000 分
    # 因為未來月份有 installment_amount 250000 分 = 2,500 元
    assert result["monthly_surplus"] < 2200000
    assert result["monthly_surplus"] == 2200000 - 250000  # 1,950,000 分 = 19,500 元


def test_savings_goal_api_target_date(client, db):
    """POST /planning/savings-goal API 整合測試：target_date 模式。"""
    from app.models.account import Account
    from app.models.income import Income
    from app.models.obligation import Obligation

    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    db.add(Income(name="薪水", amount=5000000, frequency="monthly",
                  start_date=date(2026, 1, 5), next_date=date(2026, 4, 5)))
    db.add(Obligation(name="房租", type="fixed", amount=2000000, frequency="monthly",
                      start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1)))
    db.commit()

    resp = client.post("/api/v1/planning/savings-goal", json={
        "target_amount": 120000,  # 元
        "target_date": "2026-09-01",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["monthly_needed"] > 0
    assert data["monthly_surplus"] > 0
    assert "is_feasible" in data


def test_savings_goal_api_monthly_saving(client, db):
    """POST /planning/savings-goal API 整合測試：monthly_saving 模式。"""
    from app.models.account import Account
    from app.models.income import Income

    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    db.add(Income(name="薪水", amount=5000000, frequency="monthly",
                  start_date=date(2026, 1, 5), next_date=date(2026, 4, 5)))
    db.commit()

    resp = client.post("/api/v1/planning/savings-goal", json={
        "target_amount": 120000,
        "monthly_saving": 20000,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["months_needed"] == 6
    assert "projected_date" in data


def test_savings_goal_api_validation_neither(client):
    """必須提供 target_date 或 monthly_saving 其一 → 422。"""
    resp = client.post("/api/v1/planning/savings-goal", json={
        "target_amount": 120000,
    })
    assert resp.status_code == 422


def test_savings_goal_api_validation_both(client):
    """不可同時提供 target_date 和 monthly_saving → 422。"""
    resp = client.post("/api/v1/planning/savings-goal", json={
        "target_amount": 120000,
        "target_date": "2026-09-01",
        "monthly_saving": 20000,
    })
    assert resp.status_code == 422
