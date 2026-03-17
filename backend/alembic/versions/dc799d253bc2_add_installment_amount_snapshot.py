"""add_installment_amount_snapshot

Revision ID: dc799d253bc2
Revises: f305aa7040c0
Create Date: 2026-03-15 09:03:24.750360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc799d253bc2'
down_revision: Union[str, None] = 'f305aa7040c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('credit_card_bills', schema=None) as batch_op:
        batch_op.add_column(sa.Column('installment_amount', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('credit_card_bills', schema=None) as batch_op:
        batch_op.drop_column('installment_amount')
