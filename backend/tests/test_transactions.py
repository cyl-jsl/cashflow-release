import csv
import io

import pytest


def _make_csv_bytes(rows: list[list[str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


class TestTransactionImport:
    def test_import_csv_creates_transactions(self, client):
        csv_data = _make_csv_bytes([
            ["date", "description", "amount"],
            ["2026-03-01", "午餐", "150"],
            ["2026-03-02", "超商", "85"],
        ])
        resp = client.post(
            "/api/v1/transactions/import",
            files={"file": ("test.csv", csv_data, "text/csv")},
            data={
                "date_column": "date",
                "description_column": "description",
                "amount_column": "amount",
            },
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["transactions_created"] == 2
        assert body["total_spending"] == 235.0  # (150 + 85)

    def test_import_with_credit_card_id(self, client, db):
        # 先建信用卡
        from app.models.credit_card import CreditCard
        card = CreditCard(name="測試卡", billing_day=15, due_day=3)
        db.add(card)
        db.commit()

        csv_data = _make_csv_bytes([
            ["date", "description", "amount"],
            ["2026-03-01", "午餐", "150"],
        ])
        resp = client.post(
            "/api/v1/transactions/import",
            files={"file": ("test.csv", csv_data, "text/csv")},
            data={
                "date_column": "date",
                "description_column": "description",
                "amount_column": "amount",
                "credit_card_id": str(card.id),
            },
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["credit_card_id"] == card.id

    def test_list_transactions(self, client):
        # 先匯入
        csv_data = _make_csv_bytes([
            ["date", "description", "amount"],
            ["2026-03-01", "午餐", "150"],
        ])
        client.post(
            "/api/v1/transactions/import",
            files={"file": ("test.csv", csv_data, "text/csv")},
            data={
                "date_column": "date",
                "description_column": "description",
                "amount_column": "amount",
            },
        )
        resp = client.get("/api/v1/transactions")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_import_invalid_csv_returns_422(self, client):
        csv_data = _make_csv_bytes([
            ["date", "memo", "amount"],
            ["2026-03-01", "午餐", "150"],
        ])
        resp = client.post(
            "/api/v1/transactions/import",
            files={"file": ("test.csv", csv_data, "text/csv")},
            data={
                "date_column": "date",
                "description_column": "description",
                "amount_column": "amount",
            },
        )
        assert resp.status_code == 422

    def test_delete_by_source_file(self, client):
        csv_data = _make_csv_bytes([
            ["date", "description", "amount"],
            ["2026-03-01", "午餐", "150"],
        ])
        client.post(
            "/api/v1/transactions/import",
            files={"file": ("batch1.csv", csv_data, "text/csv")},
            data={
                "date_column": "date",
                "description_column": "description",
                "amount_column": "amount",
            },
        )
        resp = client.delete("/api/v1/transactions?source_file=batch1.csv")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] >= 1

        # 確認已刪除
        resp = client.get("/api/v1/transactions")
        assert len(resp.json()["data"]) == 0
