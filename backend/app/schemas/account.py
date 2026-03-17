from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AccountType(str, Enum):
    bank = "bank"
    cash = "cash"
    investment = "investment"


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: AccountType
    balance: float = 0  # 元（API 層）
    currency: str = "TWD"
    note: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    type: AccountType | None = None
    balance: float | None = None
    currency: str | None = None
    note: str | None = None


class AccountRead(BaseModel):
    id: int
    name: str
    type: AccountType
    balance: float  # 元
    balance_updated_at: datetime
    currency: str
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceUpdate(BaseModel):
    id: int
    balance: float  # 元


class BatchUpdateBalances(BaseModel):
    updates: list[BalanceUpdate] = Field(..., min_length=1)


def to_read(account) -> AccountRead:
    """將 ORM Account 轉為 AccountRead，金額從分轉為元。"""
    return AccountRead(
        id=account.id,
        name=account.name,
        type=account.type,
        balance=account.balance / 100,
        balance_updated_at=account.balance_updated_at,
        currency=account.currency,
        note=account.note,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )
