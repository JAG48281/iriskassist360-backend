import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def fix_ubgr_rates():
    with engine.begin() as conn:
        print("Checking for BGRP product...")
        result = conn.execute(text("SELECT id FROM product_master WHERE product_code = 'BGRP'"))
        row = result.fetchone()
        if not row:
            print("BGRP Product Not Found! Creating it?")
            # Assume it exists or fail?
            # It should exist.
            print("Looking for 'UBGR'...")
            row = conn.execute(text("SELECT id FROM product_master WHERE product_code = 'UBGR'")).fetchone()
            if not row:
                print("UBGR Product Not Found either.")
                return
        
        product_id = row[0]
        print(f"Product ID: {product_id}")
        
        # Occupancies
        occs = ['1001', '1001_2']
        for iib in occs:
            result = conn.execute(text("SELECT id FROM occupancies WHERE iib_code = :iib"), {"iib": iib})
            occ_row = result.fetchone()
            if not occ_row:
                print(f"Occupancy {iib} not found.")
                continue
                
            occ_id = occ_row[0]
            
            # Upsert Rate
            print(f"Upserting Rate 0.15 for Product {product_id} and Occupancy {occ_id} ({iib})...")
            
            # Delete existing to be safe/lazy or update?
            # Let's check for update.
            existing = conn.execute(text("""
                SELECT id FROM product_basic_rates 
                WHERE product_id = :pid AND occupancy_id = :oid
            """), {"pid": product_id, "oid": occ_id}).fetchone()
            
            if existing:
                conn.execute(text("""
                    UPDATE product_basic_rates 
                    SET basic_rate = 0.15, updated_at = now()
                    WHERE id = :rid
                """), {"rid": existing[0]})
                print("Updated existing rate.")
            else:
                conn.execute(text("""
                    INSERT INTO product_basic_rates (product_code, product_id, occupancy_id, basic_rate, created_at, updated_at)
                    VALUES ('BGRP', :pid, :oid, 0.15, now(), now())
                """), {"pid": product_id, "oid": occ_id})
                print("Inserted new rate.")

if __name__ == "__main__":
    fix_ubgr_rates()
