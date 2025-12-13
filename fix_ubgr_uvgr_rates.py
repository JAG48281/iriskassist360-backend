import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def fix_ubgr_uvgr_rates():
    with engine.begin() as conn:
        # Get product IDs
        products = conn.execute(text("SELECT id, product_code FROM product_master WHERE product_code IN ('UBGR', 'UVGR')")).fetchall()
        
        if not products:
            print("❌ UBGR/UVGR products not found!")
            return
        
        for product in products:
            product_id, product_code = product
            print(f"\nProcessing {product_code} (ID: {product_id})")
            
            # Get occupancy IDs
            occs = conn.execute(text("SELECT id, iib_code FROM occupancies WHERE iib_code IN ('1001', '1001_2')")).fetchall()
            
            for occ in occs:
                occ_id, iib_code = occ
                
                # Check if rate exists
                existing = conn.execute(text("""
                    SELECT id FROM product_basic_rates 
                    WHERE product_id = :pid AND occupancy_id = :oid
                """), {"pid": product_id, "oid": occ_id}).fetchone()
                
                if existing:
                    print(f"  Rate exists for {iib_code}")
                else:
                    # Insert rate
                    conn.execute(text("""
                        INSERT INTO product_basic_rates (product_code, product_id, occupancy_id, basic_rate, created_at, updated_at)
                        VALUES (:pc, :pid, :oid, 0.15, now(), now())
                    """), {"pc": product_code, "pid": product_id, "oid": occ_id})
                    print(f"  ✅ Inserted rate 0.15 for {iib_code}")

if __name__ == "__main__":
    fix_ubgr_uvgr_rates()
