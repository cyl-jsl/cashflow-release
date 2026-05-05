import pytest
from datetime import date

from app.models.account import Account
from app.models.income import Income
from app.models.income_adjustment import IncomeAdjustment
from app.services.forecast import calculate_available, calculate_timeline


def _make_income(name="月薪1", amount=3175800, next_date=date(2026, 5, 10)):
    """建立 monthly income，amount 預設 31758元（3175800分）。"""
    return Income(
        name=name,
        amount=amount,
        frequency="monthly",
        start_date=date(2026, 1, 10),
        next_date=next_date,
    )


def test_forecast_without_adjustment_uses_base_amount(db):
    """未建立 adjustment 時，forecast 使用 Income.amount（基準薪資）。"""
    db.add(Account(name="帳戶", type="bank", balance=0, currency="TWD"))
    income = _make_income()
    db.add(income)
    db.commit()

    result = calculate_available(
        db,
        from_date=date(2026, 5, 4),
        until_date=date(2026, 5, 10),
    )
    assert result["period_income"] == 3175800


def test_forecast_with_adjustment_uses_actual_amount(db):
    """建立 adjustment 後，指定發薪日改用 actual_amount。"""
    db.add(Account(name="帳戶", type="bank", balance=0, currency="TWD"))
    income = _make_income()
    db.add(income)
    db.flush()

    adj = IncomeAdjustment(
        income_id=income.id,
        effective_date=date(2026, 5, 10),
        actual_amount=2944800,
    )
    db.add(adj)
    db.commit()

    result = calculate_available(
        db,
        from_date=date(2026, 5, 4),
        until_date=date(2026, 5, 10),
    )
    assert result["period_income"] == 2944800


def test_forecast_future_month_still_uses_base(db):
    """已確認 5/10 實領，6/10（未確認）應仍用基準薪資。"""
    db.add(Account(name="帳戶", type="bank", balance=0, currency="TWD"))
    income = _make_income(next_date=date(2026, 5, 10))
    db.add(income)
    db.flush()

    adj = IncomeAdjustment(
        income_id=income.id,
        effective_date=date(2026, 5, 10),
        actual_amount=2944800,
    )
    db.add(adj)
    db.commit()

    result = calculate_available(
        db,
        from_date=date(2026, 6, 10),
        until_date=date(2026, 6, 10),
    )
    assert result["period_income"] == 3175800


def test_timeline_uses_adjustment_for_confirmed_month(db):
    """calculate_timeline 產出中，已確認發薪日吃 actual_amount。"""
    db.add(Account(name="帳戶", type="bank", balance=0, currency="TWD"))
    income = _make_income(next_date=date(2026, 5, 10))
    db.add(income)
    db.flush()

    adj = IncomeAdjustment(
        income_id=income.id,
        effective_date=date(2026, 5, 10),
        actual_amount=2944800,
    )
    db.add(adj)
    db.commit()

    timeline = calculate_timeline(db, months=1, granularity="monthly", as_of=date(2026, 5, 4))
    assert timeline[0]["income_total"] == 2944800


# ── API tests ──────────────────────────────────────────────────────────────


def test_upsert_income_actual_creates_new(client):
    """POST /incomes/{id}/actuals 首次呼叫建立 adjustment，回傳 actual / delta。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "月薪1", "amount": 31758, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    resp = client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10",
        "actual_amount": 29448,
        "note": "請假扣薪",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["income_id"] == income_id
    assert data["effective_date"] == "2026-05-10"
    assert data["actual_amount"] == 29448.0
    assert data["delta_amount"] == pytest.approx(-2310.0, abs=0.01)
    assert data["note"] == "請假扣薪"


def test_upsert_income_actual_overwrites_existing(client):
    """同一 (income_id, effective_date) 再次 POST → 覆寫，不建立第二筆。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "月薪1", "amount": 31758, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10",
        "actual_amount": 29448,
    })
    resp2 = client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10",
        "actual_amount": 30000,
    })
    assert resp2.status_code == 200
    assert resp2.json()["data"]["actual_amount"] == 30000.0

    list_resp = client.get(f"/api/v1/incomes/{income_id}/adjustments")
    assert len(list_resp.json()["data"]) == 1


def test_list_income_adjustments(client):
    """GET /incomes/{id}/adjustments 回傳所有 adjustments，按日期排序。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "月薪1", "amount": 31758, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10", "actual_amount": 29448,
    })
    client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-06-10", "actual_amount": 31758,
    })

    resp = client.get(f"/api/v1/incomes/{income_id}/adjustments")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 2
    assert items[0]["effective_date"] == "2026-05-10"
    assert items[1]["effective_date"] == "2026-06-10"


def test_delete_income_adjustment(client):
    """DELETE /income-adjustments/{id} 刪除後再 GET 確認消失。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "月薪1", "amount": 31758, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    adj_resp = client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10", "actual_amount": 29448,
    })
    adj_id = adj_resp.json()["data"]["id"]

    del_resp = client.delete(f"/api/v1/income-adjustments/{adj_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"] == {"deleted": adj_id}

    list_resp = client.get(f"/api/v1/incomes/{income_id}/adjustments")
    assert list_resp.json()["data"] == []


def test_delta_recomputed_after_base_amount_change(client):
    """PUT /incomes/{id} 改了基準薪資後，list 出來的 delta 應反映新基準（不能 stale）。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "月薪1", "amount": 31758, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10", "actual_amount": 29448,
    })

    client.put(f"/api/v1/incomes/{income_id}", json={"amount": 30000})

    resp = client.get(f"/api/v1/incomes/{income_id}/adjustments")
    item = resp.json()["data"][0]
    assert item["delta_amount"] == pytest.approx(-552.0, abs=0.01)


def test_upsert_income_actual_404_on_missing_income(client):
    """income_id 不存在 → 404。"""
    resp = client.post("/api/v1/incomes/9999/actuals", json={
        "effective_date": "2026-05-10", "actual_amount": 29448,
    })
    assert resp.status_code == 404


def test_upsert_once_income_returns_400(client):
    """frequency=once 的收入不允許 adjustment → 400。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "獎金", "amount": 10000, "frequency": "once",
        "start_date": "2026-05-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    resp = client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-10", "actual_amount": 9000,
    })
    assert resp.status_code == 400


def test_upsert_misaligned_effective_date_returns_400(client):
    """effective_date 不對齊 income schedule → 400（避免日期錯位永遠 hit 不到）。"""
    resp = client.post("/api/v1/incomes", json={
        "name": "月薪1", "amount": 31758, "frequency": "monthly",
        "start_date": "2026-01-10", "next_date": "2026-05-10",
    })
    income_id = resp.json()["data"]["id"]

    resp = client.post(f"/api/v1/incomes/{income_id}/actuals", json={
        "effective_date": "2026-05-15", "actual_amount": 29448,
    })
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "MISALIGNED_DATE"
