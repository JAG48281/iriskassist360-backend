"""
Emergency seed script for fire_terrorism_rates
Run this manually on Railway to populate the table
"""
import sys
sys.path.insert(0, '.')

import csv
import os
from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def emergency_seed_terrorism_rates():
    """Emergency seeding for fire_terrorism_rates using UPSERT"""
    logger.info("🚨 EMERGENCY SEED: fire_terrorism_rates")
    
    csv_path = "data/fire_terrorism_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV not found: {csv_path}")
        return False
    
    try:
        with engine.begin() as conn:
            # Check table exists
            exists = conn.execute(text("SELECT to_regclass('public.fire_terrorism_rates')")).scalar()
            if not exists:
                logger.error("❌ Table fire_terrorism_rates does not exist!")
                return False
            
            # Clear existing data (if any)
            conn.execute(text("DELETE FROM fire_terrorism_rates"))
            logger.info("Cleared existing data")
            
            # Insert from CSV
            inserted = 0
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    max_si = row.get('max_sum_insured')
                    if not max_si or max_si.strip() == '':
                        max_si = None
                    else:
                        max_si = float(max_si)
                    
                    sql = text("""
                        INSERT INTO fire_terrorism_rates 
                        (occupancy_type, min_sum_insured, max_sum_insured, rate_per_mille)
                        VALUES (:ot, :min_si, :max_si, :rate)
                    """)
                    
                    conn.execute(sql, {
                        "ot": row['occupancy_type'],
                        "min_si": float(row['min_sum_insured']),
                        "max_si": max_si,
                        "rate": float(row['rate_per_mille'])
                    })
                    inserted += 1
            
            logger.info(f"✅ Inserted {inserted} rows into fire_terrorism_rates")
            
            # Verify
            count = conn.execute(text("SELECT COUNT(*) FROM fire_terrorism_rates")).scalar()
            logger.info(f"✅ Final count: {count} rows")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = emergency_seed_terrorism_rates()
    sys.exit(0 if success else 1)
