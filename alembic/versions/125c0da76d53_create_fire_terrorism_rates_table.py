"""create fire_terrorism_rates table

Revision ID: 125c0da76d53
Revises: 7bcbffe8ee3c
Create Date: 2025-12-18 10:57:42.518050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '125c0da76d53'
down_revision: Union[str, None] = '7bcbffe8ee3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy import inspect

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table('fire_terrorism_rates'):
        print("DEBUG: Creating fire_terrorism_rates in 125c")
        op.create_table(
            'fire_terrorism_rates',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
            sa.Column('occupancy_type', sa.String(length=30), nullable=False),
            sa.Column('min_sum_insured', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0'),
            sa.Column('max_sum_insured', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('rate_per_mille', sa.Numeric(precision=6, scale=4), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )

def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'fire_terrorism_rates' in inspector.get_table_names():
        op.drop_table('fire_terrorism_rates')

