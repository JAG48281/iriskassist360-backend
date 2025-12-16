import csv
import os
import sys
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def seed_bsus_rates():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_bsus_rates.csv')
    print(f"Reading CSV from: {csv_path}")
    
    with engine.begin() as conn:
        # Step 1: Create Table
        print("Creating Table fire_bsus_rates...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fire_bsus_rates (
                iib_code VARCHAR(20) NOT NULL,
                eq_zone VARCHAR(20) NOT NULL,
                rate_per_mille NUMERIC(10,4) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (iib_code, eq_zone)
            );
        """))

        # Step 2: Create Staging
        print("Creating Staging Table...")
        conn.execute(text("DROP TABLE IF EXISTS fire_bsus_rates_staging"))
        conn.execute(text("""
            CREATE TEMP TABLE fire_bsus_rates_staging (
                iib_code VARCHAR(20),
                eq_zone VARCHAR(20),
                rate_per_mille NUMERIC(10,4)
            )
        """))
        
        # Step 3: Load CSV to Staging
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Headers: iib_code, eq_zone, rate
            rows = []
            for row in reader:
                iib_code = row.get("iib_code")
                eq_zone = row.get("eq_zone")
                rate = row.get("rate")
                
                if iib_code and eq_zone and rate:
                    rows.append({
                        "iib_code": iib_code,
                        "eq_zone": eq_zone,
                        "rate_per_mille": rate
                    })
            
            print(f"Loaded {len(rows)} rows from CSV.")
            
            if rows:
                print("Inserting into staging...")
                # Chunk insert if needed, but 1200 rows is fine
                conn.execute(
                    text("INSERT INTO fire_bsus_rates_staging (iib_code, eq_zone, rate_per_mille) VALUES (:iib_code, :eq_zone, :rate_per_mille)"),
                    rows
                )
        
        # Step 4: Upsert
        print("Upserting into main table...")
        upsert_sql = """
        INSERT INTO fire_bsus_rates (iib_code, eq_zone, rate_per_mille)
        SELECT iib_code, eq_zone, rate_per_mille
        FROM fire_bsus_rates_staging
        ON CONFLICT (iib_code, eq_zone)
        DO UPDATE SET
            rate_per_mille = EXCLUDED.rate_per_mille;
        """
        conn.execute(text(upsert_sql))
        
        # Step 5: Validation
        count = conn.execute(text("SELECT COUNT(*) FROM fire_bsus_rates")).scalar()
        print(f"\nTotal rows in fire_bsus_rates: {count}")
        
        result = conn.execute(text("SELECT iib_code, eq_zone, rate_per_mille FROM fire_bsus_rates ORDER BY iib_code, eq_zone LIMIT 20"))
        print("\nValidation Sample (Top 20):")
        print("-" * 45)
        print(f"{'IIB_CODE':<10} | {'EQ_ZONE':<10} | {'RATE':<10}")
        print("-" * 45)
        for row in result:
             print(f"{row.iib_code:<10} | {row.eq_zone:<10} | {row.rate_per_mille:<10}")
        print("-" * 45)

if __name__ == "__main__":
    seed_bsus_rates()
