"""Drop strict constraints from add_on_rates

Revision ID: e0a5de259a69
Revises: 67b973da6292
Create Date: 2025-12-12 15:14:17.688822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0a5de259a69'
down_revision: Union[str, None] = '872f94033eb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL to drop constraints if they exist
    op.execute("ALTER TABLE add_on_rates DROP CONSTRAINT IF EXISTS ck_add_on_rates_rate_type")
    op.execute("ALTER TABLE add_on_rates DROP CONSTRAINT IF EXISTS uq_add_on_rates_composite")

def downgrade() -> None:
    # Re-adding them might be tricky without exact definitions, skipping strict revert for now 
    # as these caused production issues.
    pass
