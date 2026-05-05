"""add_income_adjustments_table

Revision ID: a99a5bf783c8
Revises: dc799d253bc2
Create Date: 2026-05-04 14:53:18.793425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a99a5bf783c8'
down_revision: Union[str, None] = 'dc799d253bc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "income_adjustments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "income_id",
            sa.Integer(),
            sa.ForeignKey("incomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("actual_amount", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("income_id", "effective_date", name="uq_income_adjustment"),
    )
    op.create_index(
        "ix_income_adjustments_effective_date",
        "income_adjustments",
        ["effective_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_income_adjustments_effective_date", table_name="income_adjustments")
    op.drop_table("income_adjustments")
