
from app.database import engine
from sqlalchemy import text

def fix_terrorism_schema_strict():
    with engine.connect() as conn:
        print("Fixing Terrorism Schema Strict...")
        conn.execute(text("COMMIT")) 
        
        # 1. Drop product columns if they exist
        for col in ['product_code', 'product_id']:
            try:
                conn.execute(text(f"ALTER TABLE terrorism_slabs DROP COLUMN IF EXISTS {col}"))
                print(f"Dropped {col}")
            except Exception as e:
                print(f"Error dropping {col}: {e}")

        # 2. Rename columns to match User Request exactly (si_from -> min_sum_insured)
        # Check current columns first to know what to rename
        try:
             # Try renaming from si_from (current state)
             conn.execute(text("ALTER TABLE terrorism_slabs RENAME COLUMN si_from TO min_sum_insured"))
             print("Renamed si_from -> min_sum_insured")
        except Exception as e:
             # Maybe it's si_min?
             try:
                 conn.execute(text("ALTER TABLE terrorism_slabs RENAME COLUMN si_min TO min_sum_insured"))
                 print("Renamed si_min -> min_sum_insured")
             except Exception:
                 print("Could not rename to min_sum_insured (maybe already correct?)")

        try:
             # Try renaming from si_to (current state)
             conn.execute(text("ALTER TABLE terrorism_slabs RENAME COLUMN si_to TO max_sum_insured"))
             print("Renamed si_to -> max_sum_insured")
        except Exception as e:
             # Maybe it's si_max?
             try:
                 conn.execute(text("ALTER TABLE terrorism_slabs RENAME COLUMN si_max TO max_sum_insured"))
                 print("Renamed si_max -> max_sum_insured")
             except Exception:
                 print("Could not rename to max_sum_insured (maybe already correct?)")

        conn.commit()
        print("Schema Update Complete.")

if __name__ == "__main__":
    fix_terrorism_schema_strict()
