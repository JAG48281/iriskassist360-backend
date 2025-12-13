"""merge_heads

Revision ID: a100416aa0e0
Revises: 8517faee5760, e0a5de259a69
Create Date: 2025-12-13 23:05:42.134804

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a100416aa0e0'
down_revision: Union[str, None] = ('8517faee5760', 'e0a5de259a69')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
