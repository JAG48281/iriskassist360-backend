from sqlalchemy import create_engine, text, inspect
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def safe_cleanup():
    print("Checking new table status...")
    with engine.connect() as conn:
        try:
            count_iib = conn.execute(text("SELECT COUNT(*) FROM fire_iib_rates")).scalar()
            count_bsus = conn.execute(text("SELECT COUNT(*) FROM fire_bsus_rates")).scalar()
            
            print(f"fire_iib_rates count: {count_iib}")
            print(f"fire_bsus_rates count: {count_bsus}")
            
            if count_iib == 0 or count_bsus == 0:
                print("CRITICAL: One of the new tables is empty. ABORTING CLEANUP.")
                return
                
        except Exception as e:
            print(f"Error checking new tables: {e}")
            return

    # Check for obsolete tables and drop
    obsolete_tables = ["product_basic_rates", "generic_rate_master", "irisk_rates"]
    
    inspector = inspect(engine)
    existing = inspector.get_table_names()
    
    print("\nDropping obsolete tables...")
    with engine.begin() as conn:
        for table in obsolete_tables:
            if table in existing:
                print(f"Dropping {table}...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            else:
                print(f"{table} not found (already clean).")

    # Final Verification
    print("\nRemaining Tables in public schema:")
    inspector = inspect(engine)
    final_tables = inspector.get_table_names()
    for t in final_tables:
        print(f"- {t}")

if __name__ == "__main__":
    safe_cleanup()
