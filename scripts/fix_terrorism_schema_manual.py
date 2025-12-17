
from app.database import engine
from sqlalchemy import text

def fix_schema():
    with engine.connect() as conn:
        print("Fixing Schema...")
        conn.execute(text("COMMIT")) # Ensure no transaction
        
        # 1. Drop product_code if exists
        try:
            conn.execute(text("ALTER TABLE terrorism_slabs DROP COLUMN IF EXISTS product_code"))
            print("Dropped product_code")
        except Exception as e:
            print(f"Error dropping product_code: {e}")
            
        # 2. Rename si_min -> si_from
        try:
            conn.execute(text("ALTER TABLE terrorism_slabs RENAME COLUMN si_min TO si_from"))
            print("Renamed si_min -> si_from")
        except Exception as e:
            print(f"Error renaming si_min (maybe already done?): {e}")

        # 3. Rename si_max -> si_to
        try:
            conn.execute(text("ALTER TABLE terrorism_slabs RENAME COLUMN si_max TO si_to"))
            print("Renamed si_max -> si_to")
        except Exception as e:
            print(f"Error renaming si_max: {e}")
            
        conn.commit()
        print("Schema Fix Complete.")
        
        # 4. Insert Test Slab (Residential, 10L -> 0.10)
        # Clear existing to be clean? Or just add?
        # Let's add carefully.
        try:
            conn.execute(text("""
                DELETE FROM terrorism_slabs WHERE occupancy_type='Residential' AND si_from=0
            """))
            conn.execute(text("""
                INSERT INTO terrorism_slabs (occupancy_type, si_from, si_to, rate_per_mille, created_at, updated_at)
                VALUES ('Residential', 0, 50000000, 0.10, NOW(), NOW())
            """))
            conn.commit()
            print("Seeded Test Slab: Residential 0-5Cr -> 0.10")
        except Exception as e:
            print(f"Seeding failed: {e}")

if __name__ == "__main__":
    fix_schema()
