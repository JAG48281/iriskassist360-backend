import csv
import os
import sys
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def seed_stfi_rates():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_stfi_rates.csv')
    print(f"Reading CSV from: {csv_path}")
    
    with engine.begin() as conn:
        # Step 1: Create Table
        print("Creating Table fire_stfi_rates...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fire_stfi_rates (
                iib_code VARCHAR(20) PRIMARY KEY,
                stfi_rate_per_mille NUMERIC(10,4) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Step 2: Create Staging
        print("Creating Staging Table...")
        conn.execute(text("DROP TABLE IF EXISTS fire_stfi_rates_staging"))
        conn.execute(text("""
            CREATE TEMP TABLE fire_stfi_rates_staging (
                iib_code VARCHAR(20),
                stfi_rate_per_mille NUMERIC(10,4)
            )
        """))
        
        # Step 3: Load CSV to Staging
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Headers: iib_code, stfi_rate
            rows = []
            for row in reader:
                iib_code = row.get("iib_code")
                rate = row.get("stfi_rate")
                
                if iib_code and rate:
                    rows.append({
                        "iib_code": iib_code,
                        "stfi_rate_per_mille": rate
                    })
            
            print(f"Loaded {len(rows)} rows from CSV.")
            
            if rows:
                print("Inserting into staging...")
                conn.execute(
                    text("INSERT INTO fire_stfi_rates_staging (iib_code, stfi_rate_per_mille) VALUES (:iib_code, :stfi_rate_per_mille)"),
                    rows
                )
        
        # Step 4: Upsert
        print("Upserting into main table...")
        upsert_sql = """
        INSERT INTO fire_stfi_rates (iib_code, stfi_rate_per_mille)
        SELECT iib_code, stfi_rate_per_mille
        FROM fire_stfi_rates_staging
        ON CONFLICT (iib_code)
        DO UPDATE SET
            stfi_rate_per_mille = EXCLUDED.stfi_rate_per_mille;
        """
        conn.execute(text(upsert_sql))
        
        # Step 5: Validation
        count = conn.execute(text("SELECT COUNT(*) FROM fire_stfi_rates")).scalar()
        print(f"\nTotal rows in fire_stfi_rates: {count}")
        
        # Check NULLs
        null_count = conn.execute(text("SELECT COUNT(*) FROM fire_stfi_rates WHERE stfi_rate_per_mille IS NULL")).scalar()
        if null_count > 0:
             print(f"FAILED: Found {null_count} NULL rates!")
        else:
             print("PASS: No NULL rates.")

        # Check Duplicates
        dup_count = conn.execute(text("SELECT iib_code, COUNT(*) FROM fire_stfi_rates GROUP BY iib_code HAVING COUNT(*) > 1")).fetchall()
        if dup_count:
             print(f"FAILED: Found {len(dup_count)} duplicates!")
        else:
             print("PASS: No duplicates.")
        
        # Sample Check
        sample = conn.execute(text("SELECT * FROM fire_stfi_rates WHERE iib_code = '1002'")).fetchone()
        if sample:
             print(f"Sample 1002: {sample.stfi_rate_per_mille} (Expected 0.22)")
        else:
             print("Sample 1002: NOT FOUND")

if __name__ == "__main__":
    seed_stfi_rates()
