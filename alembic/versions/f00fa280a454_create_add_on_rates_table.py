"""create add_on_rates table

Revision ID: f00fa280a454
Revises: 907ba2fd3a36
Create Date: 2025-12-11 18:31:41.082947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f00fa280a454'
down_revision: Union[str, None] = '907ba2fd3a36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'add_on_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('add_on_id', sa.Integer(), nullable=False),
        sa.Column('product_code', sa.String(length=50), nullable=False),
        sa.Column('occupancy_type', sa.String(length=50), nullable=True),
        sa.Column('si_min', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('si_max', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('rate_type', sa.String(length=30), nullable=False),
        sa.Column('rate_value', sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['add_on_id'], ['add_on_master.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('add_on_id', 'product_code', 'occupancy_type', 'si_min', 'si_max', name='uq_add_on_rates_composite')
    )
    op.create_check_constraint(
        'ck_add_on_rates_rate_type',
        'add_on_rates',
        "rate_type IN ('flat', 'percentage', 'per_mille')"
    )
    op.create_check_constraint(
        'ck_add_on_rates_occupancy_type',
        'add_on_rates',
        "occupancy_type IS NULL OR occupancy_type IN ('Residential', 'Non-Industrial', 'Industrial')"
    )


def downgrade() -> None:
    op.drop_table('add_on_rates')
