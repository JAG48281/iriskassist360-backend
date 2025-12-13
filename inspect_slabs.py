import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def inspect_slabs():
    with engine.connect() as conn:
        # Standard select
        result = conn.execute(text("""
            SELECT t.id, t.rate_per_mille, p.product_code, t.occupancy_type
            FROM terrorism_slabs t
            JOIN product_master p ON t.product_id = p.id
            WHERE p.product_code = 'BGRP'
        """))
        rows = result.fetchall()
        print(f"Found {len(rows)} rows for BGRP:")
        for r in rows:
            print(r)

if __name__ == "__main__":
    inspect_slabs()
