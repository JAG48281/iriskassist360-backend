import csv
import os
import sys
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def seed_fire_add_on_master():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_add_on_master.csv')
    print(f"Reading CSV from: {csv_path}")
    
    with engine.begin() as conn:
        # Step 1: Create Table
        print("Creating Table fire_add_on_master...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fire_add_on_master (
                add_on_code VARCHAR(50) PRIMARY KEY,
                add_on_name TEXT NOT NULL,
                description TEXT,
                rate_type VARCHAR(20) NOT NULL,
                applies_to BOOLEAN DEFAULT TRUE,
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
                description TEXT,
                rate_type VARCHAR(20),
                applies_to BOOLEAN,
                is_active BOOLEAN
            )
        """))
        
        # Step 3: Load CSV to Staging
        rows_to_insert = []
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # CSV Cols: add_on_code,add_on_name,description,is_percentage,applies_to_product,active
                
                for row in reader:
                    code = row.get("add_on_code")
                    name = row.get("add_on_name")
                    desc = row.get("description")
                    is_pct = row.get("is_percentage", "FALSE").strip().upper() == "TRUE"
                    applies = row.get("applies_to_product", "TRUE").strip().upper() == "TRUE"
                    active = row.get("active", "TRUE").strip().upper() == "TRUE"
                    
                    rate_type = "percentage" if is_pct else "flat"
                    
                    if code:
                        rows_to_insert.append({
                            "code": code,
                            "name": name,
                            "desc": desc,
                            "rtype": rate_type,
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
                    (add_on_code, add_on_name, description, rate_type, applies_to, is_active)
                    VALUES (:code, :name, :desc, :rtype, :applies, :active)
                """),
                rows_to_insert
            )
        
        # Step 4: Upsert to Main Table
        print("Upserting into main table...")
        upsert_sql = """
        INSERT INTO fire_add_on_master (add_on_code, add_on_name, description, rate_type, applies_to, is_active)
        SELECT add_on_code, add_on_name, description, rate_type, applies_to, is_active
        FROM fire_add_on_master_staging
        ON CONFLICT (add_on_code)
        DO UPDATE SET
            add_on_name = EXCLUDED.add_on_name,
            description = EXCLUDED.description,
            rate_type = EXCLUDED.rate_type,
            applies_to = EXCLUDED.applies_to,
            is_active = EXCLUDED.is_active;
        """
        conn.execute(text(upsert_sql))
        
        # Step 5: Verification
        count = conn.execute(text("SELECT COUNT(*) FROM fire_add_on_master")).scalar()
        print(f"Total rows in fire_add_on_master: {count}")
        
        # Sample Check
        sample = conn.execute(text("SELECT * FROM fire_add_on_master LIMIT 1")).fetchone()
        if sample:
            print(f"Sample: {sample.add_on_code} - {sample.add_on_name} ({sample.rate_type})")

if __name__ == "__main__":
    seed_fire_add_on_master()
