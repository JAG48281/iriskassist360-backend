from sqlalchemy import text
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def setup_fire_iib_rates():
    # 1. DDL
    ddl = """
    CREATE TABLE IF NOT EXISTS fire_iib_rates (
        iib_code VARCHAR(20) PRIMARY KEY,
        rate_per_mille NUMERIC(10,4) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 2. Sample Data (using upsert for re-run safety)
    sample_data = """
    INSERT INTO fire_iib_rates (iib_code, rate_per_mille) VALUES
    ('1001', 0.22),
    ('1001_2', 0.22),
    ('2001', 0.35)
    ON CONFLICT (iib_code) DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille;
    """
    
    # 3. Verify
    verify_sql = "SELECT iib_code, rate_per_mille FROM fire_iib_rates ORDER BY iib_code;"

    try:
        with engine.begin() as conn: # Transactional
            print("Creating table fire_iib_rates...")
            conn.execute(text(ddl))
            
            print("Inserting sample data...")
            conn.execute(text(sample_data))
            
            print("Verifying data...")
            result = conn.execute(text(verify_sql))
            rows = result.fetchall()
            
            print("\n[VERIFICATION] fire_iib_rates content:")
            print("-" * 30)
            print(f"{'IIB_CODE':<15} | {'RATE':<10}")
            print("-" * 30)
            for row in rows:
                print(f"{row.iib_code:<15} | {row.rate_per_mille:<10}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_fire_iib_rates()
