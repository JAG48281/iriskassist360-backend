import csv
import os
import sys
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def seed_fire_add_on_rates_special():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_add_on_rates.csv')
    print(f"Reading CSV from: {csv_path}")
    
    with engine.begin() as conn:
        # Step 1: Create Table
        print("Creating Table fire_add_on_rates...")
        conn.execute(text("DROP TABLE IF EXISTS fire_add_on_rates CASCADE"))
        conn.execute(text("""
            CREATE TABLE fire_add_on_rates (
                id SERIAL PRIMARY KEY,
                add_on_code VARCHAR(50) NOT NULL,
                product_group TEXT NOT NULL,
                pricing_type VARCHAR(50) NOT NULL,
                rate_value NUMERIC(10,4) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (add_on_code, product_group)
            );
        """))
        
        # Step 2: Create Staging
        conn.execute(text("DROP TABLE IF EXISTS fire_add_on_rates_staging"))
        conn.execute(text("""
            CREATE TEMP TABLE fire_add_on_rates_staging (
                add_on_code VARCHAR(50),
                product_group TEXT,
                pricing_type VARCHAR(50),
                rate_value NUMERIC(10,4),
                is_active BOOLEAN
            )
        """)) # Removed UNIQUE so staging doesn't fail on dupes immediately -> actually logic will handle filtering

        # Step 3: Load Data
        rows_to_insert = []
        valid_types = ["FLAT", "PER_MILLE", "COMPOSITE_PERCENT", "TOTAL_RATE_PERCENT"]
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # Cols: add_on_code,product_group,pricing_type,rate_value,is_active
                
                for row in reader:
                    code = row.get("add_on_code", "").strip()
                    pgroup = row.get("product_group", "").strip()
                    ptype = row.get("pricing_type", "").strip().upper()
                    if ptype == "AUTHORITY": ptype = "AUTHORIT" # Just in case, but usually rejected
                    
                    rate_str = row.get("rate_value")
                    active = row.get("is_active", "TRUE").strip().upper() == "TRUE"
                    
                    if not code:
                        continue
                        
                    # Rule: Reject invalid pricing_type (FREE/AUTHORIT are ignored here)
                    if ptype not in valid_types:
                        # Log explicit rejection only for debug
                        # print(f"Skipping {code} type {ptype} (Not special pricing)")
                        continue
                        
                    if not rate_str:
                        print(f"Skipping {code}: rate_value is NULL/Empty")
                        continue
                        
                    try:
                        rate_val = float(rate_str)
                    except ValueError:
                        print(f"Skipping {code}: Invalid rate {rate_str}")
                        continue
                        
                    rows_to_insert.append({
                        "c": code,
                        "pg": pgroup,
                        "pt": ptype,
                        "r": rate_val,
                        "a": active
                    })
        except FileNotFoundError:
            print("CSV not found.")
            return

        print(f"Loaded {len(rows_to_insert)} valid special pricing rows.")
        
        if rows_to_insert:
            conn.execute(
                text("""
                    INSERT INTO fire_add_on_rates_staging (add_on_code, product_group, pricing_type, rate_value, is_active)
                    VALUES (:c, :pg, :pt, :r, :a)
                """),
                rows_to_insert
            )
            
            # Transfer to main
            # Using DO UPDATE for conflicts if csv has dupes (though (code, pgroup) should be unique)
            print("Upserting to fire_add_on_rates...")
            conn.execute(text("""
                INSERT INTO fire_add_on_rates (add_on_code, product_group, pricing_type, rate_value, is_active)
                SELECT add_on_code, product_group, pricing_type, rate_value, is_active
                FROM fire_add_on_rates_staging
                ON CONFLICT (add_on_code, product_group)
                DO UPDATE SET
                    pricing_type = EXCLUDED.pricing_type,
                    rate_value = EXCLUDED.rate_value,
                    is_active = EXCLUDED.is_active
            """))
            
        # Verify
        count = conn.execute(text("SELECT COUNT(*) FROM fire_add_on_rates")).scalar()
        print(f"Total rows in fire_add_on_rates: {count}")
        
        sample = conn.execute(text("SELECT * FROM fire_add_on_rates LIMIT 1")).fetchone()
        if sample:
            print(f"Sample: {sample.add_on_code} / {sample.product_group} -> {sample.rate_value} ({sample.pricing_type})")

if __name__ == "__main__":
    seed_fire_add_on_rates_special()
