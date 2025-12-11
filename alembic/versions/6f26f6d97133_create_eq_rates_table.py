"""create eq_rates table

Revision ID: 6f26f6d97133
Revises: 6120b75f0964
Create Date: 2025-12-11 18:14:28.158125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f26f6d97133'
down_revision: Union[str, None] = '6120b75f0964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'eq_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('occupancy_id', sa.Integer(), nullable=False),
        sa.Column('eq_zone', sa.String(length=20), nullable=False),
        sa.Column('eq_rate', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['occupancy_id'], ['occupancies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('occupancy_id', 'eq_zone', name='uq_eq_rates_occupancy_zone')
    )


def downgrade() -> None:
    op.drop_table('eq_rates')
