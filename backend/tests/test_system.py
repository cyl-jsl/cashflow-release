from datetime import date


def test_advance_cycles(client):
    """POST /system/advance-cycles 推進過期週期"""
    client.post("/api/v1/incomes", json={
        "name": "薪水", "amount": 50000, "frequency": "monthly",
        "start_date": "2025-01-05", "next_date": "2025-01-05",
    })
    resp = client.post("/api/v1/system/advance-cycles")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["incomes_advanced"] > 0


def test_load_sample_data(client):
    """POST /system/load-sample-data 載入範例資料"""
    resp = client.post("/api/v1/system/load-sample-data")
    assert resp.status_code == 200
    # 驗證有帳戶被建立
    accounts = client.get("/api/v1/accounts").json()["data"]
    assert len(accounts) > 0
    # 驗證有收入被建立
    incomes = client.get("/api/v1/incomes").json()["data"]
    assert len(incomes) > 0
