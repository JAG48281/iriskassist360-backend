"""create_and_seed_fire_add_on_master

Revision ID: 729a329b77b5
Revises: 381d5fd0eb8a
Create Date: 2025-12-16 16:34:36.527095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '729a329b77b5'
down_revision: Union[str, None] = '381d5fd0eb8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import csv
import os
from sqlalchemy.sql import text

def upgrade() -> None:
    # 1. Create Table
    op.create_table(
        'fire_add_on_master',
        sa.Column('add_on_code', sa.String(length=50), nullable=False),
        sa.Column('add_on_name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rate_type', sa.String(length=20), nullable=False),
        sa.Column('applies_to', sa.Boolean(), server_default='true', nullable=True),
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
            # CSV Cols: add_on_code,add_on_name,description,is_percentage,applies_to_product,active
            for row in reader:
                code = row.get("add_on_code")
                name = row.get("add_on_name")
                desc = row.get("description")
                is_pct = row.get("is_percentage", "FALSE").strip().upper() == "TRUE"
                applies = row.get("applies_to_product", "TRUE").strip().upper() == "TRUE"
                active = row.get("active", "TRUE").strip().upper() == "TRUE"
                
                rate_type = "percentage" if is_pct else "flat"
                
                if code:
                    # Escape single quotes in text fields
                    safe_name = name.replace("'", "''") if name else ""
                    safe_desc = desc.replace("'", "''") if desc else ""
                    
                    rows.append(
                        f"('{code}', '{safe_name}', '{safe_desc}', '{rate_type}', {str(applies).upper()}, {str(active).upper()})"
                    )
    except FileNotFoundError:
        print(f"Warning: CSV file not found at {csv_path}. Skipping seed.")
        return

    if not rows:
        return

    # Use raw SQL for bulk upsert (Single Batch ~50 rows)
    chunk_size = 300
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        values = ", ".join(chunk)
        
        sql = f"""
        INSERT INTO fire_add_on_master (add_on_code, add_on_name, description, rate_type, applies_to, is_active)
        VALUES {values}
        ON CONFLICT (add_on_code) 
        DO UPDATE SET
            add_on_name = EXCLUDED.add_on_name,
            description = EXCLUDED.description,
            rate_type = EXCLUDED.rate_type,
            applies_to = EXCLUDED.applies_to,
            is_active = EXCLUDED.is_active;
        """
        op.execute(sql)


def downgrade() -> None:
    op.drop_table('fire_add_on_master')
