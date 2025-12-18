"""add_uq_fire_terrorism_rates

Revision ID: 37d757b24e92
Revises: adf47baee5fa
Create Date: 2025-12-18 12:17:44.558726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d757b24e92'
down_revision: Union[str, None] = 'adf47baee5fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint to support UPSERT
    op.create_unique_constraint(
        'uq_fire_terrorism_rates_occ_min_si',
        'fire_terrorism_rates',
        ['occupancy_type', 'min_sum_insured']
    )

def downgrade() -> None:
    op.drop_constraint('uq_fire_terrorism_rates_occ_min_si', 'fire_terrorism_rates', type_='unique')
