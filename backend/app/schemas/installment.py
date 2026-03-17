from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class InstallmentCreate(BaseModel):
    """嵌入 ObligationCreate 中使用，建立 type=installment 的 Obligation 時一併提供。"""
    credit_card_id: int
    total_amount: float = Field(..., gt=0)  # 元
    total_periods: int = Field(..., gt=0)
    interest_rate: float | None = None
    fee: float | None = None  # 元
    # M3: bill installment
    installment_type: str = "purchase"  # "purchase" | "bill"
    source_bill_id: int | None = None  # required when installment_type="bill"

    @model_validator(mode="after")
    def validate_bill_fields(self):
        if self.installment_type == "bill" and self.source_bill_id is None:
            raise ValueError("帳單分期必須提供 source_bill_id")
        if self.installment_type != "bill" and self.source_bill_id is not None:
            raise ValueError("非帳單分期不可提供 source_bill_id")
        if self.installment_type not in ("purchase", "bill"):
            raise ValueError("installment_type 必須為 purchase 或 bill")
        return self


class InstallmentRead(BaseModel):
    id: int
    obligation_id: int
    credit_card_id: int
    installment_type: str
    total_amount: float  # 元
    monthly_amount: float  # 元
    total_periods: int
    remaining_periods: int
    interest_rate: float | None
    fee: float | None  # 元
    current_period_date: date
    source_bill_id: int | None = None
    effective_from_period: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def to_read(inst) -> InstallmentRead:
    return InstallmentRead(
        id=inst.id,
        obligation_id=inst.obligation_id,
        credit_card_id=inst.credit_card_id,
        installment_type=inst.installment_type,
        total_amount=inst.total_amount / 100,
        monthly_amount=inst.monthly_amount / 100,
        total_periods=inst.total_periods,
        remaining_periods=inst.remaining_periods,
        interest_rate=float(inst.interest_rate) if inst.interest_rate is not None else None,
        fee=inst.fee / 100 if inst.fee is not None else None,
        current_period_date=inst.current_period_date,
        source_bill_id=inst.source_bill_id,
        effective_from_period=inst.effective_from_period,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )
