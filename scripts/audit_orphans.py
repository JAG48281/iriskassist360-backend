
import sys
import os
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def audit_orphans():
    print("AUDIT: Checking for orphaned add_on_rates...")
    with engine.connect() as conn:
        orphans = conn.execute(text("""
            SELECT r.add_on_code, r.product_group 
            FROM fire_add_on_rates r
            LEFT JOIN fire_add_on_master m ON r.add_on_code = m.add_on_code
            WHERE m.add_on_code IS NULL
        """)).fetchall()
        
        if not orphans:
            print("No orphans found.")
        else:
            print(f"Found {len(orphans)} orphans:")
            for o in orphans:
                print(f" - Code: {o.add_on_code}, Group: {o.product_group}")

if __name__ == "__main__":
    audit_orphans()
