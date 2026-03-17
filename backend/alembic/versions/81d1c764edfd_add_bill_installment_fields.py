"""add_bill_installment_fields

Revision ID: 81d1c764edfd
Revises: 0419cc11bf54
Create Date: 2026-03-15 04:19:04.132313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81d1c764edfd'
down_revision: Union[str, None] = '0419cc11bf54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("installments") as batch_op:
        batch_op.add_column(sa.Column("source_bill_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("effective_from_period", sa.Date(), nullable=True))
        batch_op.create_foreign_key(
            "fk_installments_source_bill_id",
            "credit_card_bills",
            ["source_bill_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("installments") as batch_op:
        batch_op.drop_constraint("fk_installments_source_bill_id", type_="foreignkey")
        batch_op.drop_column("effective_from_period")
        batch_op.drop_column("source_bill_id")
