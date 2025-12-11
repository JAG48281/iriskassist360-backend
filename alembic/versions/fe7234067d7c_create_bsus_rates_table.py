"""create bsus_rates table

Revision ID: fe7234067d7c
Revises: f31a5714099b
Create Date: 2025-12-11 18:06:02.456917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe7234067d7c'
down_revision: Union[str, None] = 'f31a5714099b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bsus_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('occupancy_type', sa.String(length=50), nullable=False),
        sa.Column('eq_zone', sa.String(length=20), nullable=False),
        sa.Column('basic_rate', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_bsus_rates_occupancy_eq', 'bsus_rates', ['occupancy_type', 'eq_zone'])
    op.create_check_constraint(
        'ck_bsus_rates_occupancy_type',
        'bsus_rates',
        "occupancy_type IN ('Residential', 'Non-Industrial', 'Industrial')"
    )


def downgrade() -> None:
    op.drop_table('bsus_rates')
