
import sys
import os
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def drop_legacy_table():
    print("Dropping legacy add_on_master...")
    try:
        with engine.begin() as conn:
             conn.execute(text("DROP TABLE IF EXISTS add_on_master CASCADE"))
        print("[SUCCESS] Dropped add_on_master.")
    except Exception as e:
        print(f"[ERROR] Failed to drop table: {e}")

if __name__ == "__main__":
    drop_legacy_table()
