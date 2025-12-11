"""create product_basic_rates table

Revision ID: f31a5714099b
Revises: 0c4068cc8965
Create Date: 2025-12-11 17:59:48.271604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f31a5714099b'
down_revision: Union[str, None] = '0c4068cc8965'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_basic_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_code', sa.String(length=20), nullable=False),
        sa.Column('occupancy_id', sa.Integer(), nullable=False),
        sa.Column('basic_rate', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['occupancy_id'], ['occupancies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_code', 'occupancy_id', name='uq_product_basic_rates_product_occupancy')
    )


def downgrade() -> None:
    op.drop_table('product_basic_rates')
