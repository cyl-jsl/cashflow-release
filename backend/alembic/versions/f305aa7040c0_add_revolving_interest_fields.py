"""add_revolving_interest_fields

Revision ID: f305aa7040c0
Revises: e469b3b2c81c
Create Date: 2026-03-15 05:38:35.272685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f305aa7040c0'
down_revision: Union[str, None] = 'e469b3b2c81c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("credit_cards") as batch_op:
        batch_op.add_column(sa.Column("revolving_interest_rate", sa.Numeric(), nullable=True))

    with op.batch_alter_table("credit_card_bills") as batch_op:
        batch_op.add_column(sa.Column("paid_amount", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("carried_forward", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("credit_card_bills") as batch_op:
        batch_op.drop_column("carried_forward")
        batch_op.drop_column("paid_amount")

    with op.batch_alter_table("credit_cards") as batch_op:
        batch_op.drop_column("revolving_interest_rate")
