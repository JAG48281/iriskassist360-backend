"""create occupancies table

Revision ID: 0c4068cc8965
Revises: d2ee20518c83
Create Date: 2025-12-11 16:58:54.218649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c4068cc8965'
down_revision: Union[str, None] = 'd2ee20518c83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'occupancies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('iib_code', sa.String(length=20), nullable=False),
        sa.Column('section_aift', sa.String(length=20), nullable=False),
        sa.Column('occupancy_type', sa.String(length=100), nullable=False),
        sa.Column('occupancy_description', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_occupancies_iib_code', 'occupancies', ['iib_code'])
    op.create_check_constraint(
        'ck_occupancies_occupancy_type',
        'occupancies',
        "occupancy_type IN ('Residential', 'Non-Industrial', 'Industrial')"
    )


def downgrade() -> None:
    op.drop_table('occupancies')
