"""add_transactions_table

Revision ID: e469b3b2c81c
Revises: 81d1c764edfd
Create Date: 2026-03-15 05:34:26.096910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e469b3b2c81c'
down_revision: Union[str, None] = '81d1c764edfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),  # 分，正數=支出
        sa.Column("credit_card_id", sa.Integer(), sa.ForeignKey("credit_cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("source_file", sa.String(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_transactions_date", "transactions", ["date"])
    op.create_index("ix_transactions_credit_card_id", "transactions", ["credit_card_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_credit_card_id", table_name="transactions")
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_table("transactions")
