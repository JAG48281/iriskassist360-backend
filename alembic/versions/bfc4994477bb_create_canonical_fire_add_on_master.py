"""create_canonical_fire_add_on_master

Revision ID: bfc4994477bb
Revises: 729a329b77b5
Create Date: 2025-12-16 17:49:12.516973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfc4994477bb'
down_revision: Union[str, None] = '729a329b77b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import csv
import os
from sqlalchemy.sql import text

def upgrade() -> None:
    # 1. Re-Create Table with Requested Schema
    # Drop existing to ensure schema change (previous step created it with different columns)
    op.execute("DROP TABLE IF EXISTS fire_add_on_master CASCADE")
    
    op.create_table(
        'fire_add_on_master',
        sa.Column('add_on_code', sa.String(length=50), nullable=False),
        sa.Column('add_on_name', sa.Text(), nullable=False),
        sa.Column('pricing_type', sa.String(length=50), nullable=False),
        sa.Column('minimum_amount', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True),
        sa.Column('applies_to', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('add_on_code')
    )

    # 2. Seed Data
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'fire_add_on_master.csv'
    )
    
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # CSV Cols: add_on_code,add_on_name,pricing_type,minimum_premium,applies_to_products,is_active
            
            seen_codes = set()
            
            for row in reader:
                code = row.get("add_on_code", "").strip()
                name = row.get("add_on_name")
                ptype = row.get("pricing_type", "").strip().upper()
                if ptype == "AUTHORITY": ptype = "AUTHORIT"
                
                min_amt_str = row.get("minimum_premium", "0")
                min_amt = float(min_amt_str) if min_amt_str else 0.0
                
                applies = row.get("applies_to_products")
                active_str = row.get("is_active", "TRUE")
                active = active_str.strip().upper() == "TRUE"
                
                if not code or code in seen_codes:
                    continue
                seen_codes.add(code)
                
                # Logic Rules validation
                if ptype == "FREE" and min_amt != 0: min_amt = 0
                if ptype == "AUTHORIT" and min_amt < 5: min_amt = 5
                
                # Escape SQL
                safe_name = name.replace("'", "''") if name else ""
                safe_applies = applies.replace("'", "''") if applies else ""
                
                rows.append(
                    f"('{code}', '{safe_name}', '{ptype}', {min_amt}, '{safe_applies}', {str(active).upper()})"
                )
    except FileNotFoundError:
        print(f"Warning: CSV file not found at {csv_path}. Skipping seed.")
        return

    if not rows:
        return

    # Use raw SQL for bulk upsert
    chunk_size = 200
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        values = ", ".join(chunk)
        
        sql = f"""
        INSERT INTO fire_add_on_master (add_on_code, add_on_name, pricing_type, minimum_amount, applies_to, is_active)
        VALUES {values}
        ON CONFLICT (add_on_code) 
        DO UPDATE SET
            add_on_name = EXCLUDED.add_on_name,
            pricing_type = EXCLUDED.pricing_type,
            minimum_amount = EXCLUDED.minimum_amount,
            applies_to = EXCLUDED.applies_to,
            is_active = EXCLUDED.is_active;
        """
        op.execute(sql)


def downgrade() -> None:
    # Restore old schema if needed, or just drop
    op.drop_table('fire_add_on_master')
    # NOTE: To fully revert to previous state, we would need to recreate the table with old schema columns (rate_type, description etc).
    # For now, drop is sufficient for cleanup.
    pass
