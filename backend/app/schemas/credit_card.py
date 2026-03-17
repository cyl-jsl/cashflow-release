from datetime import datetime

from pydantic import BaseModel, Field


class CreditCardCreate(BaseModel):
    name: str = Field(..., min_length=1)
    billing_day: int = Field(..., ge=1, le=28)
    due_day: int = Field(..., ge=1, le=28)
    credit_limit: float | None = None  # 元
    note: str | None = None
    revolving_interest_rate: float | None = None  # 年利率，如 0.15 = 15%


class CreditCardUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    billing_day: int | None = Field(None, ge=1, le=28)
    due_day: int | None = Field(None, ge=1, le=28)
    credit_limit: float | None = None
    note: str | None = None
    revolving_interest_rate: float | None = None


class CreditCardRead(BaseModel):
    id: int
    name: str
    billing_day: int
    due_day: int
    credit_limit: float | None
    note: str | None
    revolving_interest_rate: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def to_read(card) -> CreditCardRead:
    return CreditCardRead(
        id=card.id,
        name=card.name,
        billing_day=card.billing_day,
        due_day=card.due_day,
        credit_limit=card.credit_limit / 100 if card.credit_limit is not None else None,
        note=card.note,
        revolving_interest_rate=float(card.revolving_interest_rate) if card.revolving_interest_rate is not None else None,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )
