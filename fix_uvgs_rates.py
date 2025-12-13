import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def fix_uvgs_rates():
    with engine.begin() as conn:
        print("Obtaining Product ID for UVGS...")
        result = conn.execute(text("SELECT id FROM product_master WHERE product_code = 'UVGS'"))
        row = result.fetchone()
        if not row:
            print("UVGS Product Not Found!")
            return
        
        product_id = row[0]
        
        occs = ['1001', '1001_2']
        for iib in occs:
            result = conn.execute(text("SELECT id FROM occupancies WHERE iib_code = :iib"), {"iib": iib})
            occ_row = result.fetchone()
            if not occ_row:
                print(f"Occupancy {iib} not found.")
                continue
            
            occ_id = occ_row[0]
            
            # Check existing
            existing = conn.execute(text("""
                SELECT id FROM product_basic_rates 
                WHERE product_id = :pid AND occupancy_id = :oid
            """), {"pid": product_id, "oid": occ_id}).fetchone()
            
            if existing:
                print(f"Updating rate for UVGS + {iib} to 0.15")
                conn.execute(text("""
                    UPDATE product_basic_rates 
                    SET basic_rate = 0.15, updated_at = now()
                    WHERE id = :rid
                """), {"rid": existing[0]})
            else:
                print(f"Inserting rate for UVGS + {iib} as 0.15")
                conn.execute(text("""
                    INSERT INTO product_basic_rates (product_code, product_id, occupancy_id, basic_rate, created_at, updated_at)
                    VALUES ('UVGS', :pid, :oid, 0.15, now(), now())
                """), {"pid": product_id, "oid": occ_id})

if __name__ == "__main__":
    fix_uvgs_rates()
