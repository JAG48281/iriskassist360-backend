import json
import os
import sys
from sqlalchemy import text
from app.database import SessionLocal, engine
from seed import seed_add_on_rates

def run_verification():
    results = {
        "expected_rows": 121,
        "found_rows": 0,
        "per_product_counts": {},
        "null_rate_rows": 0,
        "action_taken": "none",
        "errors": []
    }

    try:
        with SessionLocal() as db:
            # 1. Total Rows
            total = db.execute(text("SELECT COUNT(*) FROM add_on_rates")).scalar()
            results["found_rows"] = total

            # 2. Rows per product
            rows = db.execute(text("SELECT product_code, COUNT(*) FROM add_on_rates GROUP BY product_code ORDER BY product_code")).fetchall()
            results["per_product_counts"] = {r[0]: r[1] for r in rows}

            # 3. Null checks
            nulls = db.execute(text("SELECT COUNT(*) FROM add_on_rates WHERE rate_value IS NULL")).scalar()
            results["null_rate_rows"] = nulls

            print("--- Verification Check 1 ---")
            print(f"Total: {total}")
            print(f"Per Product: {results['per_product_counts']}")
            print(f"Nulls: {nulls}")

            # 3b. Sample rows
            print("\n--- Sample Rows ---")
            samples = db.execute(text("SELECT id, add_on_id, product_code, rate_type, rate_value FROM add_on_rates ORDER BY id LIMIT 10")).fetchall()
            for s in samples:
                print(s)

            # Logic
            if total != 121:
                print("\nMISMATCH DETECTED. Re-running seed_add_on_rates...")
                results["action_taken"] = "reseeded"
                
                # Re-run seeding specifically
                # We need a connection object for seed functions usually
                with engine.begin() as conn:
                    seed_add_on_rates(conn)
                
                # Re-verify
                total_2 = db.execute(text("SELECT COUNT(*) FROM add_on_rates")).scalar()
                results["found_rows"] = total_2
                
                rows_2 = db.execute(text("SELECT product_code, COUNT(*) FROM add_on_rates GROUP BY product_code ORDER BY product_code")).fetchall()
                results["per_product_counts"] = {r[0]: r[1] for r in rows_2}
                
                if total_2 != 121:
                    results["errors"].append(f"Still mismatch after re-seed. Found {total_2}")

            if results["found_rows"] == 121 and results["null_rate_rows"] == 0:
                print("\nVERIFICATION SUCCESS")
            else:
                print("\nVERIFICATION FAILED")

    except Exception as e:
        results["errors"].append(str(e))
        import traceback
        traceback.print_exc()

    print("\n\nJSON_SUMMARY_START")
    print(json.dumps(results, indent=2))
    print("JSON_SUMMARY_END")

if __name__ == "__main__":
    run_verification()
