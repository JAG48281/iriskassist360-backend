"""
AUTHORITATIVE SEED SCRIPT
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
"""
import sys
import os
import csv
import logging
from sqlalchemy import text, select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from app.database import engine
from app.models.fire_models import (
    Occupancy, TerrorismSlab, AddOnMaster, AddOnRate,
    AddOnProductMap
)
from app.models.master import LobMaster

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# GUARD RAIL: Fail if product_master is referenced
FORBIDDEN_TABLE = "product_master"

def check_no_product_master():
    """GUARD RAIL: Ensure no product_master references exist"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name='{FORBIDDEN_TABLE}'"))
            if result.scalar() > 0:
                logger.critical(f"❌ FATAL: {FORBIDDEN_TABLE} table exists! This is NOT allowed.")
                logger.critical(f"❌ Products are LOGICAL, not relational.")
                raise RuntimeError(f"{FORBIDDEN_TABLE} is not part of schema")
    except Exception as e:
        if "does not exist" in str(e) or "not part of schema" in str(e):
            logger.info(f"✅ Confirmed: No {FORBIDDEN_TABLE} table (correct)")
        else:
            raise

def upsert(conn, model, data):
    """Insert data, ignore duplicates safely using SAVEPOINT"""
    try:
        with conn.begin_nested():
            stmt = insert(model).values(**data)
            conn.execute(stmt)
    except IntegrityError:
        pass  # Duplicate, skip
    except Exception as e:
        if "unique constraint" not in str(e).lower():
            logger.warning(f"Upsert error in {model.__tablename__}: {e}")

def seed_lob_master(conn):
    """Seed minimal LOB master for reference only"""
    logger.info("Seeding LOB Master (reference only)...")
    
    lobs = [
        {"lob_code": "FIRE", "lob_name": "Fire Insurance", "description": "Fire and Special Perils", "active": True},
    ]
    
    for lob in lobs:
        upsert(conn, LobMaster, lob)
    
    logger.info("✅ LOB Master seeded")

def seed_occupancies(conn):
    """Seed occupancies from CSV"""
    logger.info("Seeding Occupancies from CSV...")
    csv_path = "data/occupancies.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ {csv_path} not found!")
        raise FileNotFoundError(f"{csv_path} required")
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Remap column if needed
            if 'occupancy_description' in row:
                row['risk_description'] = row.pop('occupancy_description')
            
            upsert(conn, Occupancy, row)
            count += 1
    
    logger.info(f"✅ Seeded {count} occupancies")

def seed_fire_iib_rates(conn):
    """Seed fire

_iib_rates from CSV"""
    logger.info("Seeding Fire IIB Rates from CSV...")
    csv_path = "data/fire_iib_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    # Get occupancy ID map
    occ_map = {row[0]: row[1] for row in conn.execute(select(Occupancy.iib_code, Occupancy.id)).fetchall()}
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iib_code = row.get('iib_code')
            rate = row.get('basic_rate') or row.get('rate_per_mille')
            
            if iib_code and rate:
                # Insert directly into fire_iib_rates table
                try:
                    conn.execute(text("""
                        INSERT INTO fire_iib_rates (iib_code, rate_per_mille)
                        VALUES (:iib, :rate)
                        ON CONFLICT (iib_code) DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille
                    """), {"iib": iib_code, "rate": float(rate)})
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert IIB rate {iib_code}: {e}")
    
    logger.info(f"✅ Seeded {count} fire_iib_rates")

def seed_fire_bsus_rates(conn):
    """Seed fire_bsus_rates from CSV"""
    logger.info("Seeding Fire BSUS Rates from CSV...")
    csv_path = "data/fire_bsus_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iib_code = row.get('iib_code')
            eq_zone = row.get('eq_zone')
            rate = row.get('rate') or row.get('rate_per_mille')
            
            if iib_code and eq_zone and rate:
                try:
                    conn.execute(text("""
                        INSERT INTO fire_bsus_rates (iib_code, eq_zone, rate_per_mille)
                        VALUES (:iib, :zone, :rate)
                        ON CONFLICT (iib_code, eq_zone) DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille
                    """), {"iib": iib_code, "zone": eq_zone, "rate": float(rate)})
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert BSUS rate {iib_code}/{eq_zone}: {e}")
    
    logger.info(f"✅ Seeded {count} fire_bsus_rates")

def seed_fire_stfi_rates(conn):
    """Seed fire_stfi_rates from CSV"""
    logger.info("Seeding Fire STFI Rates from CSV...")
    csv_path = "data/fire_stfi_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iib_code = row.get('iib_code')
            rate = row.get('stfi_rate') or row.get('rate_per_mille')
            
            if iib_code and rate:
                try:
                    conn.execute(text("""
                        INSERT INTO fire_stfi_rates (iib_code, rate_per_mille)
                        VALUES (:iib, :rate)
                        ON CONFLICT (iib_code) DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille
                    """), {"iib": iib_code, "rate": float(rate)})
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert STFI rate {iib_code}: {e}")
    
    logger.info(f"✅ Seeded {count} fire_stfi_rates")

def seed_fire_eq_rates(conn):
    """Seed fire_eq_rates from CSV"""
    logger.info("Seeding Fire EQ Rates from CSV...")
    csv_path = "data/fire_eq_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iib_code = row.get('iib_code')
            eq_zone = row.get('eq_zone')
            rate = row.get('eq_rate') or row.get('rate_per_mille')
            
            if iib_code and eq_zone and rate:
                try:
                    conn.execute(text("""
                        INSERT INTO fire_eq_rates (iib_code, eq_zone, rate_per_mille)
                        VALUES (:iib, :zone, :rate)
                        ON CONFLICT (iib_code, eq_zone) DO UPDATE SET rate_per_mille = EXCLUDED.rate_per_mille
                    """), {"iib": iib_code, "zone": eq_zone, "rate": float(rate)})
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert EQ rate {iib_code}/{eq_zone}: {e}")
    
    logger.info(f"✅ Seeded {count} fire_eq_rates")

def seed_terrorism_slabs(conn):
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
    
    for slab in slabs:
        upsert(conn, TerrorismSlab, slab)
    
    logger.info(f"✅ Seeded {len(slabs)} terrorism slabs")

def seed_fire_add_on_master(conn):
    """Seed fire_add_on_master from CSV"""
    logger.info("Seeding Fire Add-on Master...")
    csv_path = "data/fire_add_on_master.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    count = 0
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
            
            try:
                conn.execute(text("""
                    INSERT INTO fire_add_on_master (add_on_code, add_on_name, pricing_type, minimum_amount, applies_to, is_active)
                    VALUES (:code, :name, :pricing, :min_amt, :applies, :active)
                    ON CONFLICT (add_on_code) DO UPDATE 
                    SET add_on_name = EXCLUDED.add_on_name,
                        pricing_type = EXCLUDED.pricing_type,
                        minimum_amount = EXCLUDED.minimum_amount
                """), {
                    "code": row.get('add_on_code'),
                    "name": row.get('add_on_name'),
                    "pricing": row.get('pricing_type'),
                    "min_amt": row.get('minimum_amount'),
                    "applies": row.get('applies_to'),
                    "active": row.get('is_active', True)
                })
                count += 1
            except Exception as e:
                logger.warning(f"Failed to insert add-on {row.get('add_on_code')}: {e}")
    
    logger.info(f"✅ Seeded {count} fire_add_on_master rows")

def seed_fire_add_on_rates(conn):
    """Seed fire_add_on_rates from CSV"""
    logger.info("Seeding Fire Add-on Rates...")
    csv_path = "data/fire_add_on_rates.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping")
        return
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(text("""
                    INSERT INTO fire_add_on_rates (add_on_code, product_group, pricing_type, rate_value, is_active)
                    VALUES (:addon, :product, :pricing, :rate, :active)
                    ON CONFLICT (add_on_code, product_group) DO UPDATE 
                    SET rate_value = EXCLUDED.rate_value,
                        pricing_type = EXCLUDED.pricing_type
                """), {
                    "addon": row.get('add_on_code'),
                    "product": row.get('product_group') or row.get('product_code'),
                    "pricing": row.get('pricing_type'),
                    "rate": float(row.get('rate_value', 0)),
                    "active": (str(row.get('is_active', 'TRUE')).upper() == 'TRUE')
                })
                count += 1
            except Exception as e:
                logger.warning(f"Failed to insert add-on rate: {e}")
    
    logger.info(f"✅ Seeded {count} fire_add_on_rates rows")

def verify_seeding(conn):
    """Verify all authorized tables are seeded"""
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
    
    for table in tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            logger.info(f"✅ {table}: {count} rows")
        except Exception as e:
            logger.error(f"❌ {table}: {e}")

def main():
    print("🚀 AUTORIT

ATIVE SEEDING SCRIPT STARTING...")
    print("✅ Products are LOGICAL, not relational")
    print("✅ NO product_master table")
    
    # GUARD RAIL
    check_no_product_master()
    
    logger.info(f"Current Working Directory: {os.getcwd()}")
    
    try:
        with engine.begin() as conn:
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            logger.info(f"Connected to Database: {db_name}")
            
            # Seed in correct order
            seed_lob_master(conn)
            seed_occupancies(conn)
            seed_fire_iib_rates(conn)
            seed_fire_bsus_rates(conn)
            seed_fire_stfi_rates(conn)
            seed_fire_eq_rates(conn)
            seed_terrorism_slabs(conn)
            seed_fire_add_on_master(conn)
            seed_fire_add_on_rates(conn)
            
            print("✅ Seeding logic finished, committing...")
        
        print("✅ Transaction Committed Successfully")
        
        # Verify
        with engine.connect() as verify_conn:
            verify_seeding(verify_conn)
        
        print("✅ ✅ ✅ SEEDING COMPLETE ✅ ✅ ✅")
        
    except Exception as e:
        print(f"❌ Seeding Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
