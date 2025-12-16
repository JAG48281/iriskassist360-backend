"""drop_irisk_rates_final_cleanup

Revision ID: 5f67847b9e6e
Revises: ef430ae7e2b6
Create Date: 2025-12-16 15:14:30.540864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f67847b9e6e'
down_revision: Union[str, None] = 'ef430ae7e2b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop remaining legacy tables
    op.execute("DROP TABLE IF EXISTS irisk_rates CASCADE")
    op.execute("DROP TABLE IF EXISTS generic_rate_master CASCADE")
    op.execute("DROP TABLE IF EXISTS generic_rate_tables CASCADE")
    op.execute("DROP TABLE IF EXISTS bsus_rates CASCADE") # Redundant safety check

def downgrade() -> None:
    pass # No restore Logic intended for cleanup
