
import sys
import os
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def validate_orphans_zero():
    print("Validating orphan count...")
    
    with engine.connect() as conn:
        count = conn.execute(text("""
            SELECT COUNT(*) 
            FROM fire_add_on_rates r
            LEFT JOIN fire_add_on_master m ON r.add_on_code = m.add_on_code
            WHERE m.add_on_code IS NULL
        """)).scalar()
        
        print(f"Orphan Count: {count}")
        
        if count == 0:
            print("[PASS] No orphans found.")
        else:
            print(f"[FAIL] Found {count} orphans!")
            sys.exit(1)

if __name__ == "__main__":
    validate_orphans_zero()
