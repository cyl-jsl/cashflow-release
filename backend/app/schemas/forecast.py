from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PeriodType(str, Enum):
    end_of_month = "end_of_month"
    next_payday = "next_payday"
    days = "days"


class PeriodInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: date = Field(alias="from")
    until: date


class AvailableResponse(BaseModel):
    total_balance: float
    period_income: float
    period_obligations: float
    period_credit_card_bills: float
    available_amount: float
    period: PeriodInfo


class TimelinePoint(BaseModel):
    date: date
    balance: float
    income_total: float
    obligation_total: float
    credit_card_total: float
    note: str | None = None


class TimelineResponse(BaseModel):
    timeline: list[TimelinePoint]
    granularity: str
    months: int


class SimulateRequest(BaseModel):
    monthly_income_change: float = Field(0, description="月收入增減（元，正=增加，負=減少）")
    monthly_expense_change: float = Field(0, description="月支出增減（元，正=增加，負=減少）")
    months: int = Field(6, ge=1, le=24, description="模擬月數")


class SimulateResponse(BaseModel):
    baseline: list[TimelinePoint]
    simulated: list[TimelinePoint]
    months: int
