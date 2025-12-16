from sqlalchemy import create_engine, text
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def final_cleanup():
    # Tables to drop
    tables_to_drop = [
        "product_basic_rates",
        "generic_rate_master", 
        "irisk_rates",
        "bsus_rates"
    ]

    print("Starting Final Cleanup...")
    try:
        with engine.begin() as conn:
            for table in tables_to_drop:
                print(f"Dropping table {table}...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        print("Cleanup execution finished.")
        
        # Verify
        print("\nVerifying remaining tables:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            rows = result.fetchall()
            for row in rows:
                print(f"- {row.table_name}")
                
    except Exception as e:
        print(f"Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    final_cleanup()
