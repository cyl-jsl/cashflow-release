import csv
import io
from datetime import date, datetime


def parse_csv(
    data: bytes,
    date_column: str,
    description_column: str,
    amount_column: str,
    encoding: str = "utf-8",
) -> list[dict]:
    """解析 CSV bytes，回傳標準化的交易列表。

    每筆交易包含：date (date), description (str), amount_cents (int)。
    金額單位為分（原始金額 * 100）。正數=支出，負數=收入/退款。
    """
    text = data.decode(encoding)
    reader = csv.DictReader(io.StringIO(text))

    # 驗證欄位存在
    if reader.fieldnames is None:
        raise ValueError("CSV 檔案無標頭列")
    for col in [date_column, description_column, amount_column]:
        if col not in reader.fieldnames:
            raise ValueError(f"找不到欄位：{col}")

    results = []
    for row in reader:
        raw_date = row[date_column].strip()
        raw_desc = row[description_column].strip()
        raw_amount = row[amount_column].strip()

        if not raw_date or not raw_amount:
            continue

        parsed_date = _parse_date(raw_date)
        parsed_amount = _parse_amount(raw_amount)

        results.append({
            "date": parsed_date,
            "description": raw_desc,
            "amount_cents": parsed_amount,
        })

    return results


def parse_xlsx(
    data: bytes,
    date_column: str,
    description_column: str,
    amount_column: str,
) -> list[dict]:
    """解析 Excel bytes，回傳標準化的交易列表。"""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(h).strip() if h else "" for h in rows[0]]
    for col in [date_column, description_column, amount_column]:
        if col not in headers:
            raise ValueError(f"找不到欄位：{col}")

    date_idx = headers.index(date_column)
    desc_idx = headers.index(description_column)
    amount_idx = headers.index(amount_column)

    results = []
    for row in rows[1:]:
        raw_date = row[date_idx]
        raw_desc = row[desc_idx]
        raw_amount = row[amount_idx]

        if raw_date is None or raw_amount is None:
            continue

        if isinstance(raw_date, datetime):
            parsed_date = raw_date.date()
        elif isinstance(raw_date, date):
            parsed_date = raw_date
        else:
            parsed_date = _parse_date(str(raw_date).strip())

        if isinstance(raw_amount, (int, float)):
            parsed_amount = round(raw_amount * 100)
        else:
            parsed_amount = _parse_amount(str(raw_amount).strip())

        results.append({
            "date": parsed_date,
            "description": str(raw_desc or "").strip(),
            "amount_cents": parsed_amount,
        })

    wb.close()
    return results


def _parse_date(s: str) -> date:
    """支援 2026-03-01 和 2026/03/01 兩種格式。"""
    s = s.replace("/", "-")
    return date.fromisoformat(s)


def _parse_amount(s: str) -> int:
    """解析金額字串為分。支援逗號分隔（如 1,500）。"""
    s = s.replace(",", "")
    return round(float(s) * 100)
