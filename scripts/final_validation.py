import sys
import os
import requests
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

BASE_URL = "http://localhost:8000/api/calculate"

def run_validations():
    print("=== DATABASE VALIDATIONS ===\n")
    
    with engine.connect() as conn:
        # 1. fire_iib_rates
        c_iib = conn.execute(text("SELECT COUNT(*) FROM fire_iib_rates")).scalar()
        null_iib = conn.execute(text("SELECT COUNT(*) FROM fire_iib_rates WHERE rate_per_mille IS NULL")).scalar()
        print(f"1. fire_iib_rates: Count={c_iib}, NULLs={null_iib}")
        if c_iib == 0 or null_iib > 0: print("   [FAIL]")
        else: print("   [PASS]")
        
        # 2. fire_bsus_rates
        dup_bsus = conn.execute(text("""
            SELECT iib_code, eq_zone, COUNT(*) FROM fire_bsus_rates 
            GROUP BY iib_code, eq_zone 
            HAVING COUNT(*) > 1
        """)).fetchall()
        print(f"2. fire_bsus_rates: Duplicates={len(dup_bsus)}")
        if len(dup_bsus) > 0: print("   [FAIL]")
        else: print("   [PASS]")
        
        # 3. fire_add_on_master consistency
        print("3. fire_add_on_master consistency:")
        # Check FREE pricing_type has min amount 0 or rate 0? master has min_amount
        err_free = conn.execute(text("SELECT COUNT(*) FROM fire_add_on_master WHERE pricing_type='FREE' AND minimum_amount != 0")).scalar()
        if err_free > 0: print(f"   [FAIL] Found {err_free} FREE items with amount != 0")
        else: print("   [PASS] All FREE items have amount 0")
        
        # 4. fire_add_on_rates orphans
        print("4. fire_add_on_rates orphans:")
        orphans = conn.execute(text("""
            SELECT COUNT(*) FROM fire_add_on_rates r
            LEFT JOIN fire_add_on_master m ON r.add_on_code = m.add_on_code
            WHERE m.add_on_code IS NULL
        """)).scalar()
        if orphans > 0: print(f"   [FAIL] Found {orphans} orphaned rates")
        else: print("   [PASS] No orphaned rates")

    print("\n=== API CALCULATIONS ===")
    
    cases = [
        ("UBGR 1001", {"product_code": "UBGR", "occupancy_id": 1001}, 0.15),
        ("SFSP 1001", {"product_code": "SFSP", "occupancy_id": 1001}, 0.15),
        ("BSUS 1002 Zone I", {"product_code": "BSUS", "occupancy_id": 1002, "eq_zone": "Zone I"}, 0.455)
    ]
    
    for label, payload, expected in cases:
        try:
            r = requests.post(BASE_URL, json=payload)
            if r.status_code == 200:
                rate = r.json()['data']['meta']['risk_rate']
                if float(rate) == float(expected):
                    print(f"   [PASS] {label} -> {rate}")
                else:
                    print(f"   [FAIL] {label} -> Expected {expected}, Got {rate}")
            else:
                print(f"   [FAIL] {label} -> API Error {r.status_code} {r.text}")
        except Exception as e:
            print(f"   [FAIL] {label} -> Exception {e}")

if __name__ == "__main__":
    run_validations()
