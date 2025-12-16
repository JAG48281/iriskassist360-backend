import csv
import os
import sys
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def seed_rates():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_iib_rates.csv')
    print(f"Reading CSV from: {csv_path}")
    
    with engine.begin() as conn:
        # Step 2: Create Staging
        print("Creating Staging Table...")
        conn.execute(text("DROP TABLE IF EXISTS fire_iib_rates_staging"))
        conn.execute(text("CREATE TEMP TABLE fire_iib_rates_staging (iib_code VARCHAR(20), rate_per_mille NUMERIC(10,4))"))
        
        # Step 3: Load CSV to Staging
        # Read CSV in Python
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Headers: iib_code, basic_rate
            rows = []
            for row in reader:
                iib_code = row.get("iib_code")
                if not iib_code: continue
                
                # Check known headers for rate
                bs = row.get("basic_rate") or row.get("rate_per_mille") or row.get("Rate")
                if not bs: continue
                
                rows.append({
                    "iib_code": iib_code,
                    "rate_per_mille": bs
                })
            
            print(f"Loaded {len(rows)} rows from CSV.")
            
            if rows:
                print("Inserting into staging...")
                conn.execute(
                    text("INSERT INTO fire_iib_rates_staging (iib_code, rate_per_mille) VALUES (:iib_code, :rate_per_mille)"),
                    rows
                )
        
        # Step 4: Upsert
        print("Upserting into main table...")
        upsert_sql = """
        INSERT INTO fire_iib_rates (iib_code, rate_per_mille)
        SELECT iib_code, rate_per_mille
        FROM fire_iib_rates_staging
        ON CONFLICT (iib_code)
        DO UPDATE SET
            rate_per_mille = EXCLUDED.rate_per_mille;
        """
        conn.execute(text(upsert_sql))
        
        # Step 5: Validation
        count = conn.execute(text("SELECT COUNT(*) FROM fire_iib_rates")).scalar()
        print(f"\nTotal rows in fire_iib_rates: {count}")
        
        result = conn.execute(text("SELECT iib_code, rate_per_mille FROM fire_iib_rates ORDER BY iib_code LIMIT 20"))
        print("\nValidation Sample (Top 20):")
        print("-" * 30)
        print(f"{'IIB_CODE':<15} | {'RATE':<10}")
        print("-" * 30)
        for row in result:
             print(f"{row.iib_code:<15} | {row.rate_per_mille:<10}")
        print("-" * 30)

if __name__ == "__main__":
    seed_rates()
