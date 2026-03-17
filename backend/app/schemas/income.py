from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Frequency


class IncomeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)  # 元
    frequency: Frequency
    start_date: date
    end_date: date | None = None
    next_date: date | None = None  # 預設 = start_date
    note: str | None = None

    @model_validator(mode="after")
    def default_next_date(self):
        if self.next_date is None:
            self.next_date = self.start_date
        return self


class IncomeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    amount: float | None = Field(None, gt=0)
    frequency: Frequency | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_date: date | None = None
    note: str | None = None


class IncomeRead(BaseModel):
    id: int
    name: str
    amount: float  # 元
    frequency: Frequency
    start_date: date
    end_date: date | None
    next_date: date
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def to_read(income) -> IncomeRead:
    return IncomeRead(
        id=income.id,
        name=income.name,
        amount=income.amount / 100,
        frequency=income.frequency,
        start_date=income.start_date,
        end_date=income.end_date,
        next_date=income.next_date,
        note=income.note,
        created_at=income.created_at,
        updated_at=income.updated_at,
    )
