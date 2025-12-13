import logging
from app.database import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("INSPECT_DB")

def inspect_schema_and_data():
    try:
        with engine.connect() as conn:
            # 1. Inspect Occupancies
            logger.info("--- OCCUPANCIES ---")
            rows = conn.execute(text("SELECT id, iib_code, occupancy_type FROM occupancies WHERE iib_code IN ('101', '1001')")).fetchall()
            for r in rows:
                logger.info(f"Occupancy found: {r}")

            if not any('1001' in str(r.iib_code) for r in rows):
                logger.warning("⚠️ Occupancy 1001 NOT FOUND.")
                
            # 2. Inspect Terrorism Slabs Column names to see if occupancy_code exists
            logger.info("--- TERRORISM SLABS COLUMNS ---")
            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'terrorism_slabs'")).fetchall()
            col_names = [c[0] for c in cols]
            logger.info(f"Columns: {col_names}")
            
            # 3. Check Terrorism Data
            logger.info("--- TERRORISM DATA (BGRP) ---")
            # Construct query based on available columns
            if 'occupancy_code' in col_names:
                t_rows = conn.execute(text("SELECT * FROM terrorism_slabs WHERE product_code='BGRP'")).fetchall()
            else:
                t_rows = conn.execute(text("SELECT * FROM terrorism_slabs WHERE product_code='BGRP'")).fetchall()
                
            for tr in t_rows:
                logger.info(f"Slab: {tr}")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    inspect_schema_and_data()
