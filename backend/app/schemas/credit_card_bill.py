from datetime import date, datetime

from pydantic import BaseModel, Field


class CreditCardBillCreate(BaseModel):
    credit_card_id: int
    billing_year: int = Field(..., ge=2020, le=2100)
    billing_month: int = Field(..., ge=1, le=12)
    due_date: date
    general_spending: float = 0  # 元
    is_paid: bool = False


class CreditCardBillUpdate(BaseModel):
    general_spending: float | None = None  # 元
    is_paid: bool | None = None
    due_date: date | None = None
    paid_amount: float | None = None  # 元，實際繳款金額


class CreditCardBillRead(BaseModel):
    id: int
    credit_card_id: int
    billing_year: int
    billing_month: int
    due_date: date
    installment_amount: float  # 元（存儲快照）
    general_spending: float  # 元
    total_amount: float  # 元（installment_amount + general_spending + carried_forward）
    is_paid: bool
    paid_amount: float | None  # 元
    carried_forward: float  # 元
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
