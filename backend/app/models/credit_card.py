from datetime import datetime

from sqlalchemy import Integer, String, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    billing_day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1~28
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1~28
    credit_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 分
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    revolving_interest_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)  # 年利率，如 0.15 = 15%
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
