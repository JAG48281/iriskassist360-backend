"""refresh_fire_iib_rates_from_csv

Revision ID: eb03765aefc6
Revises: 37d757b24e92
Create Date: 2025-12-18 22:44:38.151340

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import csv
import os
from pathlib import Path


# revision identifiers, used by Alembic.
revision: str = 'eb03765aefc6'
down_revision: Union[str, None] = '37d757b24e92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Safe data refresh for fire_iib_rates table.
    TRUNCATE + reload from corrected CSV (STFI contamination removed).
    """
    print("🔄 Starting fire_iib_rates data refresh...")
    
    # Step 1: TRUNCATE the table (safe, preserves structure)
    op.execute("TRUNCATE TABLE fire_iib_rates;")
    print("✅ Table truncated")
    
    # Step 2: Load corrected CSV
    csv_path = Path(__file__).parent.parent.parent / "data" / "fire_iib_rates.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    print(f"📂 Loading from: {csv_path}")
    
    # Step 3: Read and insert data
    conn = op.get_bind()
    inserted_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            iib_code = row.get('iib_code', '').strip()
            basic_rate = row.get('basic_rate', '').strip()
            
            # Skip empty rows
            if not iib_code or not basic_rate:
                continue
            
            # Insert into fire_iib_rates
            # Column mapping: basic_rate (CSV) -> rate_per_mille (DB)
            conn.execute(
                sa.text("""
                    INSERT INTO fire_iib_rates (iib_code, rate_per_mille)
                    VALUES (:iib_code, :rate_per_mille)
                """),
                {"iib_code": iib_code, "rate_per_mille": float(basic_rate)}
            )
            inserted_count += 1
    
    # Step 4: Verification
    result = conn.execute(sa.text("SELECT COUNT(*) FROM fire_iib_rates")).scalar()
    print(f"✅ Inserted {inserted_count} rows")
    print(f"✅ Verification: {result} rows in fire_iib_rates")
    
    if result != inserted_count:
        raise Exception(f"Row count mismatch! Inserted: {inserted_count}, Found: {result}")
    
    # Step 5: Explicit confirmation log
    print("✅ fire_iib_rates refreshed from corrected CSV (STFI contamination removed)")


def downgrade() -> None:
    """
    No downgrade for data refresh.
    This is a data correction, not a schema change.
    """
    print("⚠️ No downgrade available for data refresh migration")
