"""update fire_terrorism_rates schema

Revision ID: a3ad7cca4966
Revises: 125c0da76d53
Create Date: 2025-12-18 11:16:33.848064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3ad7cca4966'
down_revision: Union[str, None] = '125c0da76d53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adjust occupancy_type length
    op.alter_column('fire_terrorism_rates', 'occupancy_type',
               existing_type=sa.VARCHAR(length=30),
               type_=sa.String(length=50),
               existing_nullable=False)
    
    # Adjust rate_per_mille precision
    op.alter_column('fire_terrorism_rates', 'rate_per_mille',
               existing_type=sa.NUMERIC(precision=6, scale=4),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=False)
    
    # Ensure defaults for created_at/updated_at are correct (NOW() or CURRENT_TIMESTAMP)
    op.alter_column('fire_terrorism_rates', 'created_at',
               existing_type=sa.DateTime(),
               server_default=sa.text('NOW()'),
               existing_nullable=True)
    op.alter_column('fire_terrorism_rates', 'updated_at',
               existing_type=sa.DateTime(),
               server_default=sa.text('NOW()'),
               existing_nullable=True)


def downgrade() -> None:
    # Revert rate_per_mille precision
    op.alter_column('fire_terrorism_rates', 'rate_per_mille',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.Numeric(precision=6, scale=4),
               existing_nullable=False)
               
    # Revert occupancy_type length
    op.alter_column('fire_terrorism_rates', 'occupancy_type',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=30),
               existing_nullable=False)
