"""remove_cat_covers_from_addon_master

Revision ID: 872f94033eb3
Revises: 69461828dc46
Create Date: 2025-12-12 11:20:40.255990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '872f94033eb3'
down_revision: Union[str, None] = '69461828dc46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Remove dependencies first
    op.execute("DELETE FROM add_on_product_map WHERE add_on_id IN (SELECT id FROM add_on_master WHERE add_on_code IN ('EARTHQUAKE','STFI','TERRORISM'))")
    op.execute("DELETE FROM add_on_rates WHERE add_on_id IN (SELECT id FROM add_on_master WHERE add_on_code IN ('EARTHQUAKE','STFI','TERRORISM'))")
    # Remove from master
    op.execute("DELETE FROM add_on_master WHERE add_on_code IN ('EARTHQUAKE','STFI','TERRORISM')")


def downgrade():
    pass
