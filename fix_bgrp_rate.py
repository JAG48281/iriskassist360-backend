import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def fix_rate():
    with engine.begin() as conn:
        print("Updating BGRP Residential Rate to 0.07...")
        conn.execute(text("""
            UPDATE terrorism_slabs
            SET rate_per_mille = 0.07
            FROM product_master
            WHERE terrorism_slabs.product_id = product_master.id
            AND product_master.product_code = 'BGRP'
            AND terrorism_slabs.occupancy_type = 'Residential'
        """))
        print("Update executed.")
        
if __name__ == "__main__":
    fix_rate()
