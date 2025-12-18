"""create_and_seed_fire_bsus_rates

Revision ID: b9d1bc7dfbba
Revises: 5f67847b9e6e
Create Date: 2025-12-16 15:30:58.198819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9d1bc7dfbba'
down_revision: Union[str, None] = '5f67847b9e6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import csv
import os
from sqlalchemy.sql import text

def upgrade() -> None:
    # 1. Create Table
    op.create_table(
        'fire_bsus_rates',
        sa.Column('iib_code', sa.String(length=20), nullable=False),
        sa.Column('eq_zone', sa.String(length=20), nullable=False),
        sa.Column('rate_per_mille', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('iib_code', 'eq_zone')
    )

    # 2. Seed Data
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'fire_bsus_rates.csv'
    )
    
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get("iib_code")
                eq_zone = row.get("eq_zone")
                rate = row.get("rate")
                
                if iib_code and eq_zone and rate:
                    rows.append({
                        "iib_code": iib_code,
                        "eq_zone": eq_zone,
                        "rate_per_mille": rate
                    })
    except FileNotFoundError:
        print(f"Warning: CSV file not found at {csv_path}. Skipping seed.")
        return

    if not rows:
        return

    # Use raw SQL for bulk upsert
    values_list = []
    for r in rows:
        # Sanitize generic inputs to prevent injection if not trusted, but this is a controlled seed file
        iib = r['iib_code'].replace("'", "''")
        zone = r['eq_zone'].replace("'", "''")
        rate = r['rate_per_mille']
        values_list.append(f"('{iib}', '{zone}', {rate})")
        
    if values_list:
        chunk_size = 500
        for i in range(0, len(values_list), chunk_size):
            chunk = values_list[i:i + chunk_size]
            values = ", ".join(chunk)
            
            sql = f"""
            INSERT INTO fire_bsus_rates (iib_code, eq_zone, rate_per_mille)
            VALUES {values}
            ON CONFLICT (iib_code, eq_zone) 
            DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille;
            """
            op.execute(sql)


def downgrade() -> None:
    op.drop_table('fire_bsus_rates')
