from datetime import date

from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.services.forecast import calculate_simulated_timeline


def _setup_basic_scenario(db):
    """月收 50,000、房租 20,000、生活費 8,000。"""
    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
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


def test_simulate_no_changes(db):
    """無增減時，simulated 應與 baseline 相同。"""
    _setup_basic_scenario(db)

    result = calculate_simulated_timeline(
        db,
        monthly_income_change_cents=0,
        monthly_expense_change_cents=0,
        months=3,
        as_of=date(2026, 3, 15),
    )

    assert len(result["baseline"]) == 3
    assert len(result["simulated"]) == 3
    for b, s in zip(result["baseline"], result["simulated"]):
        assert b["balance"] == s["balance"]


def test_simulate_extra_expense(db):
    """增加月支出後，simulated balance 應低於 baseline。"""
    _setup_basic_scenario(db)

    result = calculate_simulated_timeline(
        db,
        monthly_income_change_cents=0,
        monthly_expense_change_cents=1500000,  # +15,000 元
        months=3,
        as_of=date(2026, 3, 15),
    )

    for i in range(3):
        assert result["simulated"][i]["balance"] < result["baseline"][i]["balance"]
    # 差額應累積
    diff_1 = result["baseline"][0]["balance"] - result["simulated"][0]["balance"]
    diff_2 = result["baseline"][1]["balance"] - result["simulated"][1]["balance"]
    assert diff_2 > diff_1  # 累積效果


def test_simulate_reduced_expense(db):
    """減少月支出後（如取消訂閱），simulated balance 應高於 baseline。"""
    _setup_basic_scenario(db)

    result = calculate_simulated_timeline(
        db,
        monthly_income_change_cents=0,
        monthly_expense_change_cents=-500000,  # -5,000 元
        months=3,
        as_of=date(2026, 3, 15),
    )

    for i in range(3):
        assert result["simulated"][i]["balance"] > result["baseline"][i]["balance"]


def test_simulate_extra_income(db):
    """增加月收入後，simulated balance 應高於 baseline。"""
    _setup_basic_scenario(db)

    result = calculate_simulated_timeline(
        db,
        monthly_income_change_cents=1000000,  # +10,000 元
        monthly_expense_change_cents=0,
        months=3,
        as_of=date(2026, 3, 15),
    )

    for i in range(3):
        assert result["simulated"][i]["balance"] > result["baseline"][i]["balance"]


def test_simulate_combined_changes(db):
    """同時增加收入和支出。"""
    _setup_basic_scenario(db)

    result = calculate_simulated_timeline(
        db,
        monthly_income_change_cents=2000000,   # +20,000 元
        monthly_expense_change_cents=1500000,  # +15,000 元
        months=3,
        as_of=date(2026, 3, 15),
    )

    # 淨增 5,000/月，simulated 應高於 baseline
    for i in range(3):
        assert result["simulated"][i]["balance"] > result["baseline"][i]["balance"]


def test_simulate_api(client, db):
    """POST /forecast/simulate API 整合測試。"""
    from app.models.account import Account
    from app.models.income import Income
    from app.models.obligation import Obligation

    db.add(Account(name="銀行", type="bank", balance=10000000, currency="TWD"))
    db.add(Income(name="薪水", amount=5000000, frequency="monthly",
                  start_date=date(2026, 1, 5), next_date=date(2026, 4, 5)))
    db.add(Obligation(name="生活費", type="budget", amount=800000, frequency="monthly",
                      start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1)))
    db.commit()

    resp = client.post("/api/v1/forecast/simulate", json={
        "monthly_income_change": 10000,  # 元
        "monthly_expense_change": 5000,  # 元
        "months": 3,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["baseline"]) == 3
    assert len(data["simulated"]) == 3
    # Simulated 的餘額應高於 baseline（淨增 5,000/月）
    assert data["simulated"][0]["balance"] > data["baseline"][0]["balance"]
