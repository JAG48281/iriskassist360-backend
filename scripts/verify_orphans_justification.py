
import sys
import os
import csv
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine

def verify_and_justify():
    print("VERIFICATION & JUSTIFICATION FOR ORPHANS\n")
    
    # 1. Load Master CSV Codes
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fire_add_on_master.csv')
    csv_codes = set()
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c = row.get("add_on_code")
                if c: csv_codes.add(c.strip())
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 2. Load Master Table Codes
    db_codes = set()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT add_on_code FROM fire_add_on_master")).fetchall()
        for r in rows:
            db_codes.add(r.add_on_code)
            
    # 3. Get Orphans
    orphans = []
    with engine.connect() as conn:
        orph_rows = conn.execute(text("""
            SELECT r.add_on_code 
            FROM fire_add_on_rates r
            LEFT JOIN fire_add_on_master m ON r.add_on_code = m.add_on_code
            WHERE m.add_on_code IS NULL
        """)).fetchall()
        orphans = [r.add_on_code for r in orph_rows]
        
    if not orphans:
        print("No orphans found to verify.")
        return

    # 4. Justify
    for code in orphans:
        in_csv = code in csv_codes
        in_db = code in db_codes
        
        status = "UNKNOWN"
        if not in_csv and not in_db:
            status = "Code not present in master CSV or Table"
        elif not in_csv and in_db:
             status = "Code missing from CSV but present in Table? (Inconsistent)" # Should not happen given orphan definition (Not in Table)
        elif in_csv and not in_db:
             status = "Code present in CSV but missing from Table (Sync Issue)"
             
        action = "REMOVE from rates"
        
        print(f"Code {code}: {status} -> {action}")

if __name__ == "__main__":
    verify_and_justify()
