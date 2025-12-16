"""create_fire_add_on_rates_special

Revision ID: cc1c4fed6e72
Revises: bfc4994477bb
Create Date: 2025-12-16 17:51:21.991570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc1c4fed6e72'
down_revision: Union[str, None] = 'bfc4994477bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import csv
import os
from sqlalchemy.sql import text

def upgrade() -> None:
    # 1. Create Table (Drop existing if any)
    op.execute("DROP TABLE IF EXISTS fire_add_on_rates CASCADE")
    
    op.create_table(
        'fire_add_on_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('add_on_code', sa.String(length=50), nullable=False),
        sa.Column('product_group', sa.Text(), nullable=False),
        sa.Column('pricing_type', sa.String(length=50), nullable=False),
        sa.Column('rate_value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('add_on_code', 'product_group', name='uq_add_on_rates_code_group')
    )

    # 2. Seed Data
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'fire_add_on_rates.csv'
    )
    
    rows = []
    valid_types = ["FLAT", "PER_MILLE", "COMPOSITE_PERCENT", "TOTAL_RATE_PERCENT"]
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Cols: add_on_code,product_group,pricing_type,rate_value,is_active
            
            for row in reader:
                code = row.get("add_on_code", "").strip()
                pgroup = row.get("product_group", "").strip()
                ptype = row.get("pricing_type", "").strip().upper()
                if ptype == "AUTHORITY": ptype = "AUTHORIT" 
                
                rate_str = row.get("rate_value")
                active_str = row.get("is_active", "TRUE")
                active = active_str.strip().upper() == "TRUE"
                
                if not code: continue
                if ptype not in valid_types: continue # Reject FREE/AUTHORIT/etc
                if not rate_str: continue
                
                try:
                    rate_val = float(rate_str)
                except ValueError:
                    continue
                
                # SQL Escape
                safe_pgroup = pgroup.replace("'", "''")
                
                rows.append(
                    f"('{code}', '{safe_pgroup}', '{ptype}', {rate_val}, {str(active).upper()})"
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
        INSERT INTO fire_add_on_rates (add_on_code, product_group, pricing_type, rate_value, is_active)
        VALUES {values}
        ON CONFLICT (add_on_code, product_group) 
        DO UPDATE SET
            pricing_type = EXCLUDED.pricing_type,
            rate_value = EXCLUDED.rate_value,
            is_active = EXCLUDED.is_active;
        """
        op.execute(sql)


def downgrade() -> None:
    op.drop_table('fire_add_on_rates')
