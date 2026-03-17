import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class CanISpendRequest(BaseModel):
    amount: float = Field(gt=0, description="想花的金額（元）")
    date: Optional[datetime.date] = Field(None, description="預計花費日期，預設今天")


class SpendImpact(BaseModel):
    available_before: float
    available_after: float
    period: dict  # {"from": str, "until": str}
    is_feasible: bool
    summary: str


class SavingsGoalRequest(BaseModel):
    target_amount: float = Field(gt=0, description="目標金額（元）")
    monthly_saving: Optional[float] = Field(None, gt=0, description="每月預計存入金額（元）")
    target_date: Optional[datetime.date] = Field(None, description="目標達成日期")

    @model_validator(mode="after")
    def validate_one_of(self):
        if self.monthly_saving is None and self.target_date is None:
            raise ValueError("必須提供 monthly_saving 或 target_date 其一")
        if self.monthly_saving is not None and self.target_date is not None:
            raise ValueError("monthly_saving 和 target_date 只能提供其一")
        return self


class SavingsGoalResponse(BaseModel):
    monthly_surplus: float
    monthly_needed: Optional[float] = None
    months_to_target: Optional[int] = None
    months_needed: Optional[int] = None
    projected_date: Optional[str] = None
    target_date: Optional[str] = None
    is_feasible: bool
    summary: str
