from datetime import date, datetime

from pydantic import BaseModel


class TransactionRead(BaseModel):
    id: int
    date: date
    description: str
    amount: float  # 元
    credit_card_id: int | None
    account_id: int | None
    category: str | None
    source_file: str
    imported_at: datetime

    model_config = {"from_attributes": True}


class ImportResponse(BaseModel):
    transactions_created: int
    total_spending: float  # 元，匯入交易的支出合計
    source_file: str
    credit_card_id: int | None = None


def to_read(txn) -> TransactionRead:
    return TransactionRead(
        id=txn.id,
        date=txn.date,
        description=txn.description,
        amount=txn.amount / 100,
        credit_card_id=txn.credit_card_id,
        account_id=txn.account_id,
        category=txn.category,
        source_file=txn.source_file,
        imported_at=txn.imported_at,
    )
