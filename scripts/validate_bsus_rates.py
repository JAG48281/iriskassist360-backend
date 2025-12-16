import sys
import os
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def validate_bsus_rates():
    print("Validating fire_bsus_rates table...")
    
    with engine.connect() as conn:
        # Check 1: NULL rates
        print("\n1. Checking for NULL rates...")
        null_count = conn.execute(text("SELECT COUNT(*) FROM fire_bsus_rates WHERE rate_per_mille IS NULL")).scalar()
        print(f"   Rows with NULL rates: {null_count}")
        if null_count > 0:
            print("   [FAIL] There are NULL rates!")
        else:
            print("   [PASS] No NULL rates found.")

        # Check 2: Duplicate Composite Keys
        print("\n2. Checking for duplicate keys (iib_code, eq_zone)...")
        duplicates = conn.execute(text("""
            SELECT iib_code, eq_zone, COUNT(*)
            FROM fire_bsus_rates
            GROUP BY iib_code, eq_zone
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicates:
            print(f"   [FAIL] found {len(duplicates)} duplicates:")
            for row in duplicates:
                print(f"   - Key: ({row.iib_code}, {row.eq_zone}) Count: {row[2]}")
        else:
            print("   [PASS] No duplicate keys found.")

if __name__ == "__main__":
    validate_bsus_rates()
