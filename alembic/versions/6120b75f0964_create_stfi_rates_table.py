"""create stfi_rates table

Revision ID: 6120b75f0964
Revises: fe7234067d7c
Create Date: 2025-12-11 18:10:38.293657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6120b75f0964'
down_revision: Union[str, None] = 'fe7234067d7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stfi_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('occupancy_id', sa.Integer(), nullable=False),
        sa.Column('stfi_rate', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['occupancy_id'], ['occupancies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('occupancy_id', name='uq_stfi_rates_occupancy_id')
    )


def downgrade() -> None:
    op.drop_table('stfi_rates')
