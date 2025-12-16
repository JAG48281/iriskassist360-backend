
import sys
import os
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def log_counts():
    print("=== FINAL ROW COUNTS ===")
    with engine.connect() as conn:
        c_master = conn.execute(text("SELECT COUNT(*) FROM fire_add_on_master")).scalar()
        c_rates = conn.execute(text("SELECT COUNT(*) FROM fire_add_on_rates")).scalar()
        
        print(f"fire_add_on_master: {c_master}")
        print(f"fire_add_on_rates:  {c_rates}")

if __name__ == "__main__":
    log_counts()
