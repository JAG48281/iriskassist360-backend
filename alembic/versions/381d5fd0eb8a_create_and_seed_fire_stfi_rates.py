"""create_and_seed_fire_stfi_rates

Revision ID: 381d5fd0eb8a
Revises: b9d1bc7dfbba
Create Date: 2025-12-16 15:49:19.174639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '381d5fd0eb8a'
down_revision: Union[str, None] = 'b9d1bc7dfbba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import csv
import os
from sqlalchemy.sql import text

def upgrade() -> None:
    # 1. Create Table
    op.create_table(
        'fire_stfi_rates',
        sa.Column('iib_code', sa.String(length=20), nullable=False),
        sa.Column('stfi_rate_per_mille', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('iib_code')
    )

    # 2. Seed Data
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'fire_stfi_rates.csv'
    )
    
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get("iib_code")
                rate = row.get("stfi_rate")
                
                if iib_code and rate:
                    rows.append({
                        "iib_code": iib_code,
                        "stfi_rate_per_mille": rate
                    })
    except FileNotFoundError:
        print(f"Warning: CSV file not found at {csv_path}. Skipping seed.")
        return

    if not rows:
        return

    # Use raw SQL for bulk upsert (Single Batch ~300 rows)
    values = ", ".join([
        f"('{r['iib_code']}', {r['stfi_rate_per_mille']})" for r in rows
    ])
    
    sql = f"""
    INSERT INTO fire_stfi_rates (iib_code, stfi_rate_per_mille)
    VALUES {values}
    ON CONFLICT (iib_code) 
    DO UPDATE SET stfi_rate_per_mille = EXCLUDED.stfi_rate_per_mille;
    """
    op.execute(sql)


def downgrade() -> None:
    op.drop_table('fire_stfi_rates')
