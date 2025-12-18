"""create_fire_terrorism_rates_v2

Revision ID: adf47baee5fa
Revises: a3ad7cca4966
Create Date: 2025-12-18 11:41:19.729789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adf47baee5fa'
down_revision: Union[str, None] = 'a3ad7cca4966'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old table if it exists
    op.execute("DROP TABLE IF EXISTS terrorism_slabs CASCADE")
    
    # Create new table
    op.create_table(
        'fire_terrorism_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('occupancy_type', sa.String(length=50), nullable=False),
        sa.Column('min_sum_insured', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('max_sum_insured', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('rate_per_mille', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fire_terrorism_rates_id'), 'fire_terrorism_rates', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_fire_terrorism_rates_id'), table_name='fire_terrorism_rates')
    op.drop_table('fire_terrorism_rates')
