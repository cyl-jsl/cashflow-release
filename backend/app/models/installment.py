from datetime import date, datetime

from sqlalchemy import Integer, String, Date, DateTime, Numeric, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Installment(Base):
    __tablename__ = "installments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obligation_id: Mapped[int] = mapped_column(Integer, ForeignKey("obligations.id", ondelete="CASCADE"), nullable=False)
    credit_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False)
    installment_type: Mapped[str] = mapped_column(String, nullable=False, default="purchase")  # purchase only in M1
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 分
    monthly_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 分
    total_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    fee: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 分
    current_period_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_bill_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("credit_card_bills.id", ondelete="SET NULL"), nullable=True
    )
    effective_from_period: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_installments_credit_card_period", "credit_card_id", "current_period_date"),
        Index("ix_installments_obligation_id", "obligation_id"),
    )
