"""rename occupancy_description to risk_description

Revision ID: 8517faee5760
Revises: fe7234067d7c
Create Date: 2025-12-13 23:18:28.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8517faee5760'
down_revision = 'fe7234067d7c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('occupancies') as batch_op:
        batch_op.alter_column('occupancy_description', new_column_name='risk_description')


def downgrade() -> None:
    with op.batch_alter_table('occupancies') as batch_op:
        batch_op.alter_column('risk_description', new_column_name='occupancy_description')
