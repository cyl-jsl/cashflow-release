import io
import csv
from datetime import date

import pytest

from app.services.csv_import import parse_csv, parse_xlsx


def _make_csv(rows: list[list[str]]) -> bytes:
    """建立 CSV bytes，第一列為 header。"""
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


class TestParseCsv:
    def test_basic_csv_parsing(self):
        data = _make_csv([
            ["date", "description", "amount"],
            ["2026-03-01", "午餐", "150"],
            ["2026-03-02", "超商", "85"],
        ])
        result = parse_csv(
            data,
            date_column="date",
            description_column="description",
            amount_column="amount",
        )
        assert len(result) == 2
        assert result[0]["date"] == date(2026, 3, 1)
        assert result[0]["description"] == "午餐"
        assert result[0]["amount_cents"] == 15000  # 150 * 100

    def test_negative_amount_treated_as_income(self):
        data = _make_csv([
            ["date", "description", "amount"],
            ["2026-03-01", "退款", "-200"],
        ])
        result = parse_csv(data, date_column="date", description_column="description", amount_column="amount")
        assert result[0]["amount_cents"] == -20000

    def test_skip_empty_rows(self):
        data = _make_csv([
            ["date", "description", "amount"],
            ["2026-03-01", "午餐", "150"],
            ["", "", ""],
            ["2026-03-02", "超商", "85"],
        ])
        result = parse_csv(data, date_column="date", description_column="description", amount_column="amount")
        assert len(result) == 2

    def test_missing_column_raises(self):
        data = _make_csv([
            ["date", "memo", "amount"],
            ["2026-03-01", "午餐", "150"],
        ])
        with pytest.raises(ValueError, match="找不到欄位"):
            parse_csv(data, date_column="date", description_column="description", amount_column="amount")

    def test_date_format_slash(self):
        """支援 2026/03/01 格式。"""
        data = _make_csv([
            ["date", "description", "amount"],
            ["2026/03/01", "午餐", "150"],
        ])
        result = parse_csv(data, date_column="date", description_column="description", amount_column="amount")
        assert result[0]["date"] == date(2026, 3, 1)

    def test_amount_with_comma(self):
        """支援 1,500 格式。"""
        data = _make_csv([
            ["date", "description", "amount"],
            ["2026-03-01", "機票", "1,500"],
        ])
        result = parse_csv(data, date_column="date", description_column="description", amount_column="amount")
        assert result[0]["amount_cents"] == 150000
