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


from sqlalchemy import inspect

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    print(f"DEBUG: adf4 tables: {existing_tables}")

    # Drop old table if exists (Legacy)
    if 'terrorism_slabs' in existing_tables:
        op.execute("DROP TABLE IF EXISTS terrorism_slabs CASCADE")
    
    # Idempotent creation of fire_terrorism_rates
    if not inspector.has_table('fire_terrorism_rates'):
        print("DEBUG: Creating fire_terrorism_rates in adf4")
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
    # Drop only if exists
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'fire_terrorism_rates' in inspector.get_table_names():
        op.drop_index(op.f('ix_fire_terrorism_rates_id'), table_name='fire_terrorism_rates')
        op.drop_table('fire_terrorism_rates')
