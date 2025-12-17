"""create_fire_eq_rates_table

Revision ID: 4a7f8e9d1c2b
Revises: cc1c4fed6e72
Create Date: 2025-12-17 14:58:00

CRITICAL: Creates missing fire_eq_rates table expected by backend.
This table stores earthquake zone-based rates for fire insurance products.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a7f8e9d1c2b'
down_revision: Union[str, None] = 'cc1c4fed6e72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create fire_eq_rates table for earthquake zone-based premium rates.
    
    Structure:
    - iib_code: Occupancy IIB code (FK to occupancies.iib_code)
    - eq_zone: Earthquake zone (e.g., "Zone I", "Zone II", etc.)
    - rate_per_mille: Rate per thousand of sum insured
    - Primary key: (iib_code, eq_zone) - unique combination
    """
    op.create_table(
        'fire_eq_rates',
        sa.Column('iib_code', sa.String(length=20), nullable=False),
        sa.Column('eq_zone', sa.String(length=20), nullable=False),
        sa.Column('rate_per_mille', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('iib_code', 'eq_zone', name='pk_fire_eq_rates')
    )
    
    # Create index for faster lookup by iib_code
    op.create_index('ix_fire_eq_rates_iib_code', 'fire_eq_rates', ['iib_code'])


def downgrade() -> None:
    """
    Remove fire_eq_rates table.
    """
    op.drop_index('ix_fire_eq_rates_iib_code', table_name='fire_eq_rates')
    op.drop_table('fire_eq_rates')
