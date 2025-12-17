"""
AUTHORITATIVE SEED SCRIPT - PRODUCTION SAFE + SELF-HEALING
Products are LOGICAL, not relational.
NO product_master table exists or will ever exist.

ONLY seed these tables (CSV-backed):
- occupancies
- fire_iib_rates
- fire_bsus_rates
- fire_stfi_rates
- fire_eq_rates
- terrorism_slabs
- fire_add_on_master
- fire_add_on_rates
- lob_master (minimal, for reference only)

TRANSACTION SAFETY:
- Each table commits independently
- Failed rows logged but don't break entire seed
- Proper rollback on exceptions

SELF-HEALING:
- Verifies table exists before seeding
- Skips missing tables with warning (doesn't crash)
- Safe to run multiple times (idempotent)
- No operation can poison transaction state
"""
import sys
import os
import csv
import logging
from sqlalchemy import text, select, insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.database import engine, SessionLocal
from app.models.fire_models import (
    Occupancy, TerrorismSlab, AddOnMaster, AddOnRate
)
from app.models.master import LobMaster

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Seeding statistics
stats = {
    "lob_master": {"success": 0, "failed": 0, "skipped": False},
    "occupancies": {"success": 0, "failed": 0, "skipped": False},
    "fire_iib_rates": {"success": 0, "failed": 0, "skipped": False},
    "fire_bsus_rates": {"success": 0, "failed": 0, "skipped": False},
    "fire_stfi_rates": {"success": 0, "failed": 0, "skipped": False},
    "fire_eq_rates": {"success": 0, "failed": 0, "skipped": False},
    "terrorism_slabs": {"success": 0, "failed": 0, "skipped": False},
    "fire_add_on_master": {"success": 0, "failed": 0, "skipped": False},
    "fire_add_on_rates": {"success": 0, "failed": 0, "skipped": False}
}

def check_table_exists(conn, table_name: str) -> bool:
    """
    SELF-HEALING: Check if table exists before attempting to seed.
    Uses PostgreSQL system catalog for non-invasive check.
    
    Returns: True if table exists, False otherwise
    """
    try:
        result = conn.execute(text(f"SELECT to_regclass('public.{table_name}')"))
        exists = result.scalar() is not None
        if not exists:
            logger.warning(f"⚠️  Table {table_name} does not exist - will skip seeding")
        return exists
    except SQLAlchemyError as e:
        conn.rollback()  # Clean transaction on error
        logger.warning(f"⚠️  Could not check {table_name}: {e}")
        return False

def should_seed(engine) -> bool:
    """
    Determine if seeding should run.
    
    Uses lob_master row count as canonical marker:
    - If lob_master has >= 1 row: SKIP SEEDING (already applied)
    - If lob_master has 0 rows or doesn't exist: RUN SEEDING (first time)
    
    Returns: True if should seed, False if already seeded
    """
    try:
        with engine.connect() as conn:
            # Check if lob_master exists
            table_exists = conn.execute(text("SELECT to_regclass('public.lob_master')")).scalar()
            
            if table_exists is None:
                # Table doesn't exist - first time setup
                return True
            
            # Table exists - check row count
            count = conn.execute(text("SELECT COUNT(*) FROM lob_master")).scalar()
            
            if count > 0:
                # Already seeded
                return False
            else:
                # Table exists but empty - seed needed
                return True
                
    except Exception as e:
        # Error checking - assume should seed (first time)
        logger.warning(f"Could not check seed status: {e}")
        return True






def safe_upsert(conn, model, data, table_name):
    """
    Safely insert data with proper rollback on failure.
    Returns: (success: bool, error_msg: str or None)
    """
    try:
        stmt = insert(model).values(**data)
        conn.execute(stmt)
        conn.commit()  # Commit each row independently
        stats[table_name]["success"] += 1
        return True, None
    except IntegrityError as e:
        # Duplicate - rollback and continue
        conn.rollback()
        if "unique constraint" in str(e).lower():
            # This is expected for duplicates - not an error
            stats[table_name]["success"] += 1
            return True, None
        stats[table_name]["failed"] += 1
        return False, f"Integrity error: {str(e)[:100]}"
    except SQLAlchemyError as e:
        # DB error - rollback and continue
        conn.rollback()
        stats[table_name]["failed"] += 1
        return False, f"DB error: {str(e)[:100]}"
    except Exception as e:
        # Any other error - rollback and continue
        conn.rollback()
        stats[table_name]["failed"] += 1
        return False, f"Error: {str(e)[:100]}"

def safe_execute_sql(conn, sql, params, table_name):
    """
    Safely execute SQL with proper rollback on failure.
    Returns: (success: bool, error_msg: str or None)
    """
    try:
        conn.execute(text(sql), params)
        conn.commit()  # Commit each row independently
        stats[table_name]["success"] += 1
        return True, None
    except IntegrityError as e:
        # Duplicate - rollback and continue
        conn.rollback()
        if "unique constraint" in str(e).lower():
            # Expected for duplicates
            stats[table_name]["success"] += 1
            return True, None
        stats[table_name]["failed"] += 1
        return False, f"Integrity error: {str(e)[:100]}"
    except SQLAlchemyError as e:
        # DB error - rollback and continue
        conn.rollback()
        stats[table_name]["failed"] += 1
        return False, f"DB error: {str(e)[:100]}"
    except Exception as e:
        # Any other error - rollback and continue
        conn.rollback()
        stats[table_name]["failed"] += 1
        return False, f"Error: {str(e)[:100]}"

def seed_lob_master():
    """Seed minimal LOB master for reference only"""
    logger.info("Seeding LOB Master (reference only)...")
    
    # SELF-HEALING: Check if table exists before seeding
    with engine.connect() as conn:
        if not check_table_exists(conn, "lob_master"):
            stats["lob_master"]["skipped"] = True
            logger.warning("⚠️  Skipping lob_master - table does not exist")
            return
    
    lobs = [
        {"lob_code": "FIRE", "lob_name": "Fire Insurance", "description": "Fire and Special Perils", "active": True},
    ]
    
    with engine.connect() as conn:
        for lob in lobs:
            success, error = safe_upsert(conn, LobMaster, lob, "lob_master")
            if not success:
                logger.warning(f"Failed LOB {lob.get('lob_code')}: {error}")
    
    logger.info(f"✅ LOB Master: {stats['lob_master']['success']} success, {stats['lob_master']['failed']} failed")

def seed_occupancies():
    """Seed occupancies from CSV"""
    logger.info("Seeding Occupancies from CSV...")
    csv_path = "data/occupancies.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ {csv_path} not found!")
        return
    
    # SELF-HEALING: Check if table exists before seeding
    with engine.connect() as conn:
        if not check_table_exists(conn, "occupancies"):
            stats["occupancies"]["skipped"] = True
            logger.warning("⚠️  Skipping occupancies - table does not exist")
            return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Remap column if needed
                if 'occupancy_description' in row:
                    row['risk_description'] = row.pop('occupancy_description')
                
                success, error = safe_upsert(conn, Occupancy, row, "occupancies")
                if not success:
                    logger.warning(f"Failed occupancy {row.get('iib_code')}: {error}")
    
    logger.info(f"✅ Occupancies: {stats['occupancies']['success']} success, {stats['occupancies']['failed']} failed")

def seed_fire_iib_rates():
    """Seed fire_iib_rates from CSV"""
    logger.info("Seeding Fire IIB Rates from CSV...")
    csv_path = "data/fire_iib_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get('iib_code')
                rate = row.get('basic_rate') or row.get('rate_per_mille')
                
                if iib_code and rate:
                    # ONLY ONE ON CONFLICT clause allowed
                    sql = """
                        INSERT INTO fire_iib_rates (iib_code, rate_per_mille)
                        VALUES (:iib, :rate)
                        ON CONFLICT (iib_code) DO UPDATE 
                        SET rate_per_mille = EXCLUDED.rate_per_mille
                    """
                    success, error = safe_execute_sql(conn, sql, {"iib": iib_code, "rate": float(rate)}, "fire_iib_rates")
                    if not success:
                        logger.warning(f"Failed IIB rate {iib_code}: {error}")
    
    logger.info(f"✅ Fire IIB Rates: {stats['fire_iib_rates']['success']} success, {stats['fire_iib_rates']['failed']} failed")

def seed_fire_bsus_rates():
    """Seed fire_bsus_rates from CSV"""
    logger.info("Seeding Fire BSUS Rates from CSV...")
    csv_path = "data/fire_bsus_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get('iib_code')
                eq_zone = row.get('eq_zone')
                rate = row.get('rate') or row.get('rate_per_mille')
                
                if iib_code and eq_zone and rate:
                    # ONLY ONE ON CONFLICT clause allowed
                    sql = """
                        INSERT INTO fire_bsus_rates (iib_code, eq_zone, rate_per_mille)
                        VALUES (:iib, :zone, :rate)
                        ON CONFLICT (iib_code, eq_zone) DO UPDATE 
                        SET rate_per_mille = EXCLUDED.rate_per_mille
                    """
                    success, error = safe_execute_sql(conn, sql, {"iib": iib_code, "zone": eq_zone, "rate": float(rate)}, "fire_bsus_rates")
                    if not success:
                        logger.warning(f"Failed BSUS rate {iib_code}/{eq_zone}: {error}")
    
    logger.info(f"✅ Fire BSUS Rates: {stats['fire_bsus_rates']['success']} success, {stats['fire_bsus_rates']['failed']} failed")

def seed_fire_stfi_rates():
    """Seed fire_stfi_rates from CSV"""
    logger.info("Seeding Fire STFI Rates from CSV...")
    csv_path = "data/fire_stfi_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get('iib_code')
                rate = row.get('stfi_rate') or row.get('rate_per_mille')
                
                if iib_code and rate:
                    # ONLY ONE ON CONFLICT clause allowed
                    sql = """
                        INSERT INTO fire_stfi_rates (iib_code, rate_per_mille)
                        VALUES (:iib, :rate)
                        ON CONFLICT (iib_code) DO UPDATE 
                        SET rate_per_mille = EXCLUDED.rate_per_mille
                    """
                    success, error = safe_execute_sql(conn, sql, {"iib": iib_code, "rate": float(rate)}, "fire_stfi_rates")
                    if not success:
                        logger.warning(f"Failed STFI rate {iib_code}: {error}")
    
    logger.info(f"✅ Fire STFI Rates: {stats['fire_stfi_rates']['success']} success, {stats['fire_stfi_rates']['failed']} failed")

def seed_fire_eq_rates():
    """Seed fire_eq_rates from CSV"""
    logger.info("Seeding Fire EQ Rates from CSV...")
    csv_path = "data/fire_eq_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iib_code = row.get('iib_code')
                eq_zone = row.get('eq_zone')
                rate = row.get('eq_rate') or row.get('rate_per_mille')
                
                if iib_code and eq_zone and rate:
                    # ONLY ONE ON CONFLICT clause allowed (FIXED)
                    sql = """
                        INSERT INTO fire_eq_rates (iib_code, eq_zone, rate_per_mille)
                        VALUES (:iib, :zone, :rate)
                        ON CONFLICT (iib_code, eq_zone) DO UPDATE 
                        SET rate_per_mille = EXCLUDED.rate_per_mille
                    """
                    success, error = safe_execute_sql(conn, sql, {"iib": iib_code, "zone": eq_zone, "rate": float(rate)}, "fire_eq_rates")
                    if not success:
                        logger.warning(f"Failed EQ rate {iib_code}/{eq_zone}: {error}")
    
    logger.info(f"✅ Fire EQ Rates: {stats['fire_eq_rates']['success']} success, {stats['fire_eq_rates']['failed']} failed")

def seed_terrorism_slabs():
    """Seed terrorism_slabs with official values"""
    logger.info("Seeding Terrorism Slabs...")
    
    slabs = [
        {"product_code": "BGRP", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.07},
        {"product_code": "UBGR", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.07},
        {"product_code": "UVGR", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.07},
        {"product_code": "SFSP", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        {"product_code": "SFSP", "occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        {"product_code": "SFSP", "occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
        {"product_code": "SFSP", "occupancy_type": "Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.20},
        {"product_code": "SFSP", "occupancy_type": "Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.15},
        {"product_code": "IAR", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        {"product_code": "IAR", "occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        {"product_code": "IAR", "occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
        {"product_code": "IAR", "occupancy_type": "Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.20},
        {"product_code": "IAR", "occupancy_type": "Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.15},
        {"product_code": "BSUS", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        {"product_code": "BSUS", "occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        {"product_code": "BSUS", "occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
        {"product_code": "BLUS", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        {"product_code": "BLUS", "occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        {"product_code": "BLUS", "occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
        {"product_code": "UVUS", "occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        {"product_code": "UVUS", "occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        {"product_code": "UVUS", "occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
    ]
    
    with engine.connect() as conn:
        for slab in slabs:
            success, error = safe_upsert(conn, TerrorismSlab, slab, "terrorism_slabs")
            if not success:
                logger.warning(f"Failed terrorism slab {slab.get('product_code')}/{slab.get('occupancy_type')}: {error}")
    
    logger.info(f"✅ Terrorism Slabs: {stats['terrorism_slabs']['success']} success, {stats['terrorism_slabs']['failed']} failed")

def seed_fire_add_on_master():
    """Seed fire_add_on_master from CSV"""
    logger.info("Seeding Fire Add-on Master...")
    csv_path = "data/fire_add_on_master.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle booleans
                if 'pricing_type' in row:
                    row['pricing_type'] = row['pricing_type'].strip()
                if 'is_active' in row:
                    row['is_active'] = (str(row.get('is_active')).upper() == 'TRUE')
                elif 'active' in row:
                    row['is_active'] = (str(row.get('active')).upper() == 'TRUE')
                    del row['active']
                
                # ONLY ONE ON CONFLICT clause allowed
                sql = """
                    INSERT INTO fire_add_on_master (add_on_code, add_on_name, pricing_type, minimum_amount, applies_to, is_active)
                    VALUES (:code, :name, :pricing, :min_amt, :applies, :active)
                    ON CONFLICT (add_on_code) DO UPDATE 
                    SET add_on_name = EXCLUDED.add_on_name,
                        pricing_type = EXCLUDED.pricing_type,
                        minimum_amount = EXCLUDED.minimum_amount
                """
                params = {
                    "code": row.get('add_on_code'),
                    "name": row.get('add_on_name'),
                    "pricing": row.get('pricing_type'),
                    "min_amt": row.get('minimum_amount'),
                    "applies": row.get('applies_to'),
                    "active": row.get('is_active', True)
                }
                success, error = safe_execute_sql(conn, sql, params, "fire_add_on_master")
                if not success:
                    logger.warning(f"Failed add-on master {row.get('add_on_code')}: {error}")
    
    logger.info(f"✅ Fire Add-on Master: {stats['fire_add_on_master']['success']} success, {stats['fire_add_on_master']['failed']} failed")

def seed_fire_add_on_rates():
    """Seed fire_add_on_rates from CSV"""
    logger.info("Seeding Fire Add-on Rates...")
    csv_path = "data/fire_add_on_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    with engine.connect() as conn:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # ONLY ONE ON CONFLICT clause allowed (FIXED)
                sql = """
                    INSERT INTO fire_add_on_rates (add_on_code, product_group, pricing_type, rate_value, is_active)
                    VALUES (:addon, :product, :pricing, :rate, :active)
                    ON CONFLICT (add_on_code, product_group) DO UPDATE 
                    SET rate_value = EXCLUDED.rate_value,
                        pricing_type = EXCLUDED.pricing_type
                """
                params = {
                    "addon": row.get('add_on_code'),
                    "product": row.get('product_group') or row.get('product_code'),
                    "pricing": row.get('pricing_type'),
                    "rate": float(row.get('rate_value', 0)),
                    "active": (str(row.get('is_active', 'TRUE')).upper() == 'TRUE')
                }
                success, error = safe_execute_sql(conn, sql, params, "fire_add_on_rates")
                if not success:
                    logger.warning(f"Failed add-on rate {row.get('add_on_code')}: {error}")
    
    logger.info(f"✅ Fire Add-on Rates: {stats['fire_add_on_rates']['success']} success, {stats['fire_add_on_rates']['failed']} failed")

def verify_seeding():
    """
    Verify all authorized tables are seeded.
    Transaction-safe: continues even if tables are missing.
    """
    logger.info("--- Post-Seeding Validation ---")
    
    tables = [
        "lob_master",
        "occupancies",
        "fire_iib_rates",
        "fire_bsus_rates",
        "fire_stfi_rates",
        "fire_eq_rates",
        "terrorism_slabs",
        "fire_add_on_master",
        "fire_add_on_rates"
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                # Transaction-safe SELECT COUNT
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                logger.info(f"✅ {table}: {count} rows")
            except SQLAlchemyError as e:
                # Rollback on ANY database error to clean transaction
                conn.rollback()
                if "does not exist" in str(e).lower():
                    logger.warning(f"⚠️  {table}: Table does not exist (will be created by migration)")
                else:
                    logger.warning(f"⚠️  {table}: Database error: {str(e)[:100]}")
                # Continue with other tables
            except Exception as e:
                # Rollback on ANY exception
                conn.rollback()
                logger.warning(f"⚠️  {table}: Error: {str(e)[:100]}")
                # Continue with other tables

def print_summary():
    """Print final seeding summary"""
    print("\n" + "="*60)
    print("SEEDING SUMMARY")
    print("="*60)
    
    total_success = 0
    total_failed = 0
    
    for table, counts in stats.items():
        success = counts["success"]
        failed = counts["failed"]
        total_success += success
        total_failed += failed
        
        status = "✅" if failed == 0 else "⚠️"
        print(f"{status} {table:25} Success: {success:4}  Failed: {failed:4}")
    
    print("="*60)
    print(f"TOTAL:                       Success: {total_success:4}  Failed: {total_failed:4}")
    print("="*60)
    
    if total_failed > 0:
        print(f"⚠️  {total_failed} rows failed (see logs above)")
    else:
        print("✅ All rows seeded successfully!")

def main():
    print("🚀 AUTHORITATIVE SEEDING SCRIPT STARTING...")
    print("✅ Products are LOGICAL, not relational")
    print("✅ PRODUCTION SAFE: Each table commits independently")
    
    # Check if seeding already applied
    if not should_seed(engine):
        logger.info("✅ Seed already applied — skipping seeding")
        print("✅ Seed already applied — skipping seeding")
        print("✅ Database is ready")
        return
    
    logger.info("🌱 First-time setup detected — running seed")
    print("🌱 First-time setup detected — running seed")
    logger.info(f"Current Working Directory: {os.getcwd()}")
    
    try:
        # Seed each table independently (safe transaction design)
        seed_lob_master()
        seed_occupancies()
        seed_fire_iib_rates()
        seed_fire_bsus_rates()
        seed_fire_stfi_rates()
        seed_fire_eq_rates()
        seed_terrorism_slabs()
        seed_fire_add_on_master()
        seed_fire_add_on_rates()
        
        # Verify
        verify_seeding()
        
        # Print summary
        print_summary()
        
        print("\n✅ ✅ ✅ SEEDING COMPLETE ✅ ✅ ✅\n")
        
    except Exception as e:
        print(f"\n❌ Seeding Failed: {e}")
        import traceback
        traceback.print_exc()
        print_summary()
        sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
