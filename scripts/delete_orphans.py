
import sys
import os
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def delete_orphans():
    print("Deleting orphaned add_on_rates...")
    
    with engine.begin() as conn: # Transaction
        result = conn.execute(text("""
            DELETE FROM fire_add_on_rates
            WHERE add_on_code NOT IN (
                SELECT add_on_code FROM fire_add_on_master
            )
        """))
        print(f"Deleted {result.rowcount} orphaned rows.")

if __name__ == "__main__":
    delete_orphans()
