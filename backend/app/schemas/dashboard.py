from datetime import date, datetime

from pydantic import BaseModel


class UpcomingDue(BaseModel):
    type: str  # "credit_card_bill" | "obligation"
    name: str
    amount: float  # 元
    due_date: date
    is_paid: bool | None = None  # only for bills


class StaleAccount(BaseModel):
    id: int
    name: str
    days_since_update: int


class AccountSummary(BaseModel):
    id: int
    name: str
    balance: float  # 元
    balance_updated_at: datetime
    is_stale: bool


class DashboardSummary(BaseModel):
    total_balance: float
    available_amount: float
    available_period: dict  # {"from": str, "until": str}
    accounts: list[AccountSummary]
    upcoming_dues: list[UpcomingDue]
    stale_accounts: list[StaleAccount]
