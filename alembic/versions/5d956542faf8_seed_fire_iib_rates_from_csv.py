"""seed_fire_iib_rates_from_csv

Revision ID: 5d956542faf8
Revises: 5f67847b9e6e
Create Date: 2025-12-16 15:23:14.645874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d956542faf8'
down_revision: Union[str, None] = '5f67847b9e6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import csv
import os
from sqlalchemy.sql import text

def upgrade() -> None:
    # Path to CSV - relative to this migration file
    # Migration is in alembic/versions/
    # CSV is in data/fire_iib_rates.csv
    # ../../data/fire_iib_rates.csv
    
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'fire_iib_rates.csv'
    )
    
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get("iib_code")
                rate = row.get("basic_rate") or row.get("rate_per_mille") or row.get("Rate")
                if iib_code and rate:
                    rows.append({
                        "iib_code": iib_code,
                        "rate_per_mille": rate
                    })
    except FileNotFoundError:
        print(f"Warning: CSV file not found at {csv_path}. Skipping seed.")
        return

    if not rows:
        return

    # Use raw SQL for bulk upsert
    # Assuming Postgres
    values = ", ".join([
        f"('{r['iib_code']}', {r['rate_per_mille']})" for r in rows
    ])
    
    # Chunking might be safer for large datasets, but 300 rows is small enough for one go
    sql = f"""
    INSERT INTO fire_iib_rates (iib_code, rate_per_mille)
    VALUES {values}
    ON CONFLICT (iib_code) 
    DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille;
    """
    op.execute(sql)


def downgrade() -> None:
    # Optional: Clear data or revert to baseline?
    # Usually data migrations are forward-only or we don't delete data on downgrade unless schema change.
    pass
