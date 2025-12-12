import os
import sys
import psycopg2
import json
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback for checking local db if needed, or error
        print(json.dumps({"error": "DATABASE_URL not set"}))
        sys.exit(1)

    tables = [
        "occupancies", "product_basic_rates", "stfi_rates", "eq_rates",
        "terrorism_slabs", "add_on_master", "add_on_product_map", "add_on_rates"
    ]
    results = {}
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                results[t] = cur.fetchone()[0]
            except Exception as e:
                results[t] = -1
                conn.rollback()
        
        conn.close()
        
        print(json.dumps(results))
        
        # Validation Rules
        failures = []
        
        # Rule: Occupancies < 200
        if results.get("occupancies", 0) < 200:
            failures.append(f"occupancies ({results.get('occupancies')}) < 200")
            
        # Rule: add_on_rates != 121
        val_rates = results.get("add_on_rates", 0)
        if val_rates != 121:
            failures.append(f"add_on_rates ({val_rates}) != 121")
            
        # Rule: terrorism_slabs < 50
        # NOTE: seed.py only generates 20 (4 products * 5 slabs). 
        # User requested < 50 check. This WILL fail if only 20 are present.
        val_slabs = results.get("terrorism_slabs", 0)
        if val_slabs < 50:
             failures.append(f"terrorism_slabs ({val_slabs}) < 50 (Seed generates 20)")

        if failures:
            print(f"Validation Errors: {', '.join(failures)}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
