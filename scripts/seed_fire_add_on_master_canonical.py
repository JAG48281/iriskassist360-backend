import csv
import os
import sys
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def seed_fire_add_on_master_canonical():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_add_on_master.csv')
    print(f"Reading CSV from: {csv_path}")
    
    with engine.begin() as conn:
        # Step 1: Re-Create Table with Requested Schema
        # Note: We are dropping the previous one which had different schema (rate_type instead of pricing_type)
        print("Re-creating Table fire_add_on_master...")
        conn.execute(text("DROP TABLE IF EXISTS fire_add_on_master CASCADE"))
        conn.execute(text("""
            CREATE TABLE fire_add_on_master (
                add_on_code VARCHAR(50) PRIMARY KEY,
                add_on_name TEXT NOT NULL,
                pricing_type VARCHAR(50) NOT NULL,
                minimum_amount NUMERIC(10,2) DEFAULT 0,
                applies_to TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Step 2: Create Staging
        conn.execute(text("DROP TABLE IF EXISTS fire_add_on_master_staging"))
        conn.execute(text("""
            CREATE TEMP TABLE fire_add_on_master_staging (
                add_on_code VARCHAR(50),
                add_on_name TEXT,
                pricing_type VARCHAR(50),
                minimum_amount NUMERIC(10,2),
                applies_to TEXT,
                is_active BOOLEAN
            )
        """))
        
        # Step 3: Load CSV to Staging
        rows_to_insert = []
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # CSV Cols: add_on_code,add_on_name,pricing_type,minimum_premium,applies_to_products,is_active
                
                valid_types = [
                    "FREE", "FLAT", "PER_MILLE", "AUTHORIT", "AUTHORITY", 
                    "COMPOSITE_PERCENT", "TOTAL_RATE_PERCENT"
                ]
                
                seen_codes = set()
                
                for row in reader:
                    code = row.get("add_on_code", "").strip()
                    name = row.get("add_on_name")
                    ptype = row.get("pricing_type", "").strip().upper()
                    # Map AUTHORITY to AUTHORIT if needed or accept AUTHORITY. User prompt said: "AUTHORIT" (no Y) in Enum?
                    # Prompt: "AUTHORIT". CSV: "AUTHORITY". I will normalize to AUTHORIT as per prompt ENUM rule or accept both if flexible. 
                    # Prompt says: "AUTHORIT". I will map AUTHORITY -> AUTHORIT to be strictly compliant.
                    if ptype == "AUTHORITY":
                        ptype = "AUTHORIT"
                        
                    min_amt_str = row.get("minimum_premium", "0")
                    # Handle renaming column in CSV (minimum_premium -> minimum_amount)
                    min_amt = float(min_amt_str) if min_amt_str else 0.0
                    
                    applies = row.get("applies_to_products")
                    active_str = row.get("is_active", "TRUE")
                    active = active_str.strip().upper() == "TRUE"
                    
                    # VALIDATION
                    if not code:
                        continue
                        
                    if code in seen_codes:
                        print(f"Skipping Duplicate Code: {code}")
                        continue
                    seen_codes.add(code)
                    
                    if ptype not in ["FREE", "FLAT", "PER_MILLE", "AUTHORIT", "COMPOSITE_PERCENT", "TOTAL_RATE_PERCENT"]:
                        print(f"Skipping Invalid Pricing Type: {ptype} for {code}")
                        continue
                        
                    if ptype == "FREE" and min_amt != 0:
                        print(f"Warning: FREE add-on {code} has min amount {min_amt}. Forcing to 0.")
                        min_amt = 0
                        
                    if ptype == "AUTHORIT" and min_amt < 5:
                         print(f"Warning: AUTHORIT add-on {code} has min amount {min_amt} < 5. Forcing to 5.")
                         min_amt = 5
                    
                    rows_to_insert.append({
                        "code": code,
                        "name": name,
                        "ptype": ptype,
                        "min_amt": min_amt,
                        "applies": applies,
                        "active": active
                    })
                        
        except FileNotFoundError:
            print(f"Error: {csv_path} not found.")
            return

        print(f"Loaded {len(rows_to_insert)} rows from CSV.")

        if rows_to_insert:
            conn.execute(
                text("""
                    INSERT INTO fire_add_on_master_staging 
                    (add_on_code, add_on_name, pricing_type, minimum_amount, applies_to, is_active)
                    VALUES (:code, :name, :ptype, :min_amt, :applies, :active)
                """),
                rows_to_insert
            )
        
        # Step 4: Upsert to Main Table
        print("Upserting into main table...")
        upsert_sql = """
        INSERT INTO fire_add_on_master (add_on_code, add_on_name, pricing_type, minimum_amount, applies_to, is_active)
        SELECT add_on_code, add_on_name, pricing_type, minimum_amount, applies_to, is_active
        FROM fire_add_on_master_staging
        ON CONFLICT (add_on_code)
        DO UPDATE SET
            add_on_name = EXCLUDED.add_on_name,
            pricing_type = EXCLUDED.pricing_type,
            minimum_amount = EXCLUDED.minimum_amount,
            applies_to = EXCLUDED.applies_to,
            is_active = EXCLUDED.is_active;
        """
        conn.execute(text(upsert_sql))
        
        # Step 5: Verification
        count = conn.execute(text("SELECT COUNT(*) FROM fire_add_on_master")).scalar()
        print(f"Total rows in fire_add_on_master: {count}")
        
        # Metadata logging
        stats = conn.execute(text("SELECT pricing_type, COUNT(*) FROM fire_add_on_master GROUP BY pricing_type")).fetchall()
        for s in stats:
            print(f"Type {s.pricing_type}: {s[1]}")

if __name__ == "__main__":
    seed_fire_add_on_master_canonical()
