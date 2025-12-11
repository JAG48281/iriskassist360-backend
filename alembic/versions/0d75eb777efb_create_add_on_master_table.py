"""create add_on_master table

Revision ID: 0d75eb777efb
Revises: 30a22a89464d
Create Date: 2025-12-11 18:22:24.841239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d75eb777efb'
down_revision: Union[str, None] = '30a22a89464d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'add_on_master',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('add_on_code', sa.String(length=50), nullable=False),
        sa.Column('add_on_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_percentage', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('applies_to_product', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('add_on_code', name='uq_add_on_master_add_on_code')
    )


def downgrade() -> None:
    op.drop_table('add_on_master')
