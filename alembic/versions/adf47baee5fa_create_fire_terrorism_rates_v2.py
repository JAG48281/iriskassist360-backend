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
    # Drop legacy terrorism_slabs if exists
    op.execute("DROP TABLE IF EXISTS terrorism_slabs CASCADE;")
    
    # Idempotent creation using raw SQL
    op.execute("""
    CREATE TABLE IF NOT EXISTS fire_terrorism_rates (
        id SERIAL PRIMARY KEY,
        occupancy_type VARCHAR(50) NOT NULL,
        min_sum_insured NUMERIC(18,2) NOT NULL,
        max_sum_insured NUMERIC(18,2),
        rate_per_mille NUMERIC(10,6) NOT NULL,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fire_terrorism_rates;")
