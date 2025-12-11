"""create terrorism_slabs table

Revision ID: 30a22a89464d
Revises: 6f26f6d97133
Create Date: 2025-12-11 18:19:25.286410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30a22a89464d'
down_revision: Union[str, None] = '6f26f6d97133'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'terrorism_slabs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('occupancy_type', sa.String(length=50), nullable=False),
        sa.Column('si_min', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('si_max', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('rate_per_mille', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_terrorism_slabs_type_range', 'terrorism_slabs', ['occupancy_type', 'si_min', 'si_max'])
    op.create_check_constraint(
        'ck_terrorism_slabs_occupancy_type',
        'terrorism_slabs',
        "occupancy_type IN ('Residential', 'Non-Industrial', 'Industrial')"
    )


def downgrade() -> None:
    op.drop_table('terrorism_slabs')
