from datetime import date, datetime

from sqlalchemy import Integer, Boolean, Date, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CreditCardBill(Base):
    __tablename__ = "credit_card_bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    credit_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False)
    billing_year: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_month: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    general_spending: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 分
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 分，實際繳款金額（null=未繳或全額）
    installment_amount: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # 分，分期快照
    carried_forward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 分，前期未繳本金 + 利息結轉
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("credit_card_id", "billing_year", "billing_month", name="uq_card_year_month"),
        Index("ix_credit_card_bills_due_paid", "due_date", "is_paid"),
    )
