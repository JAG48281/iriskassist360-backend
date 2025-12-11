"""create add_on_product_map table

Revision ID: 907ba2fd3a36
Revises: 0d75eb777efb
Create Date: 2025-12-11 18:24:55.142674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '907ba2fd3a36'
down_revision: Union[str, None] = '0d75eb777efb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'add_on_product_map',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('add_on_id', sa.Integer(), nullable=False),
        sa.Column('product_code', sa.String(length=50), nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['add_on_id'], ['add_on_master.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('add_on_id', 'product_code', name='uq_add_on_product_map_addon_product')
    )


def downgrade() -> None:
    op.drop_table('add_on_product_map')
