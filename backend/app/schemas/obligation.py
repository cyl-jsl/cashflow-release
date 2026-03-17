from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Frequency
from app.schemas.installment import InstallmentCreate, InstallmentRead


class ObligationType(str, Enum):
    fixed = "fixed"
    installment = "installment"
    budget = "budget"


class ObligationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: ObligationType
    amount: float = Field(..., gt=0)  # 元
    frequency: Frequency
    start_date: date
    end_date: date | None = None
    next_due_date: date | None = None
    note: str | None = None
    installment: InstallmentCreate | None = None  # required when type=installment

    @model_validator(mode="after")
    def validate_installment(self):
        if self.next_due_date is None:
            self.next_due_date = self.start_date
        if self.type == ObligationType.installment and self.installment is None:
            raise ValueError("type=installment 時必須提供 installment 明細")
        if self.type != ObligationType.installment and self.installment is not None:
            raise ValueError("非 installment 類型不可提供 installment 明細")
        return self


class ObligationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    type: ObligationType | None = None
    amount: float | None = Field(None, gt=0)
    frequency: Frequency | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_due_date: date | None = None
    note: str | None = None


class ObligationRead(BaseModel):
    id: int
    name: str
    type: ObligationType
    amount: float  # 元
    frequency: Frequency
    start_date: date
    end_date: date | None
    next_due_date: date
    note: str | None
    created_at: datetime
    updated_at: datetime
    installment: InstallmentRead | None = None

    model_config = {"from_attributes": True}


def to_read(obligation, installment=None) -> ObligationRead:
    from app.schemas.installment import to_read as inst_to_read
    return ObligationRead(
        id=obligation.id,
        name=obligation.name,
        type=obligation.type,
        amount=obligation.amount / 100,
        frequency=obligation.frequency,
        start_date=obligation.start_date,
        end_date=obligation.end_date,
        next_due_date=obligation.next_due_date,
        note=obligation.note,
        created_at=obligation.created_at,
        updated_at=obligation.updated_at,
        installment=inst_to_read(installment) if installment else None,
    )
