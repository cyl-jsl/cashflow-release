from datetime import date, datetime

from pydantic import BaseModel, Field


class IncomeAdjustmentCreate(BaseModel):
    effective_date: date
    actual_amount: float = Field(..., gt=0)
    note: str | None = None


class IncomeAdjustmentRead(BaseModel):
    id: int
    income_id: int
    effective_date: date
    actual_amount: float
    delta_amount: float
    note: str | None
    created_at: datetime
    updated_at: datetime
