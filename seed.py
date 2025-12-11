import sys
import os
import csv
import logging
from sqlalchemy import text, select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import engine, SessionLocal
from app.models.fire_models import *
from app.models.master import LobMaster, ProductMaster

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def table_has_rows(conn, table_name):
    """Check if a table has any rows."""
    try:
        query = text(f"SELECT 1 FROM {table_name} LIMIT 1")
        result = conn.execute(query).fetchone()
        return result is not None
    except Exception as e:
        logger.warning(f"Error checking table {table_name}: {e}")
        return False

def get_product_map(conn):
    """Fetch product_code -> id map."""
    query = select(ProductMaster.product_code, ProductMaster.id)
    result = conn.execute(query).fetchall()
    return {row[0]: row[1] for row in result}

def get_lob_map(conn):
    """Fetch lob_code -> id map."""
    query = select(LobMaster.lob_code, LobMaster.id)
    result = conn.execute(query).fetchall()
    return {row[0]: row[1] for row in result}

def get_occupancy_map(conn):
    """Fetch occupancy_id -> iib_code or similar?"""
    # Needed for rates that reference occupancy_id
    query = select(Occupancy.iib_code, Occupancy.id)
    result = conn.execute(query).fetchall()
    return {row[0]: row[1] for row in result}

def seed_lob_and_product(conn):
    """Seed LobMaster and ProductMaster if empty."""
    if table_has_rows(conn, "lob_master") and table_has_rows(conn, "product_master"):
        logger.info("Skipping LOB and Product seeding (Tables have data)")
        return

    logger.info("Seeding LOB and Products...")
    
    # LOBs
    lobs = [
        {"lob_code": "FIRE", "lob_name": "Fire Insurance", "description": "Fire and Special Perils", "active": True},
        {"lob_code": "MOTOR", "lob_name": "Motor Insurance", "description": "Private and Commercial Vehicles", "active": True},
        {"lob_code": "HEALTH", "lob_name": "Health Insurance", "description": "Individual and Floater policies", "active": True},
        {"lob_code": "PA", "lob_name": "Personal Accident", "description": "Individual and Group PA", "active": True},
        {"lob_code": "LIABILITY", "lob_name": "Liability Insurance", "description": "CGL, D&O, WC", "active": True},
        {"lob_code": "ENGINEERING", "lob_name": "Engineering Insurance", "description": "CAR, EAR, MBD", "active": True},
        {"lob_code": "MISC", "lob_name": "Miscellaneous", "description": "Other insurance products", "active": True},
    ]

    for lob in lobs:
        stmt = pg_insert(LobMaster).values(**lob).on_conflict_do_nothing()
        conn.execute(stmt)
    
    # Need to commit or flush to get IDs if needed, but we can just re-fetch map later or rely on sequences
    # Since we are in a transaction, we need to ensure visibility? Actually pg_insert is executed.

    lob_map_query = select(LobMaster.lob_code, LobMaster.id)
    lob_map_rows = conn.execute(lob_map_query).fetchall()
    lob_map = {row[0]: row[1] for row in lob_map_rows}

    fire_id = lob_map.get("FIRE")
    
    if not fire_id:
        logger.error("FIRE LOB ID not found after seed!")
        return

    # Products
    fire_products = [
        {"lob_id": fire_id, "product_code": "SFSP", "product_name": "Standard Fire and Special Perils", "description": "Traditional Fire Policy", "active": True},
        {"lob_id": fire_id, "product_code": "IAR", "product_name": "Industrial All Risk", "description": "Comprehensive Industrial Cover", "active": True},
        {"lob_id": fire_id, "product_code": "BGRP", "product_name": "Bharat Griha Raksha Policy", "description": "Home Insurance", "active": True},
        {"lob_id": fire_id, "product_code": "BSUSP", "product_name": "Bharat Sookshma Udyam Suraksha", "description": "Micro Enterprise", "active": True},
        {"lob_id": fire_id, "product_code": "BLUSP", "product_name": "Bharat Laghu Udyam Suraksha", "description": "Small Enterprise", "active": True},
        {"lob_id": fire_id, "product_code": "VUSP", "product_name": "Value Udyam", "description": "Value Added Product", "active": True},
        {"lob_id": fire_id, "product_code": "UBGR", "product_name": "Bharat Griha Raksha (UIIC)", "description": "UIIC Specific Home Insurance", "active": True},
    ]

    for prod in fire_products:
        stmt = pg_insert(ProductMaster).values(**prod).on_conflict_do_nothing()
        conn.execute(stmt)

def seed_occupancies(conn):
    if table_has_rows(conn, "occupancies"):
        logger.info("Skipping Occupancies (Data exists)")
        return
    
    logger.info("Seeding Occupancies...")
    csv_path = "data/occupancies.csv"
    data = []
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
    else:
        # Minimal Sample
        data = [
            {"iib_code": "101", "section_aift": "1", "occupancy_type": "Residential", "occupancy_description": "Residential Buildings"},
            {"iib_code": "201", "section_aift": "2", "occupancy_type": "Non-Industrial", "occupancy_description": "Offices"},
            {"iib_code": "301", "section_aift": "3", "occupancy_type": "Industrial", "occupancy_description": "General Manufacturing"}
        ]
        
    for row in data:
        stmt = pg_insert(Occupancy).values(**row).on_conflict_do_nothing()
        conn.execute(stmt)

def seed_product_basic_rates(conn):
    if table_has_rows(conn, "product_basic_rates"):
        logger.info("Skipping ProductBasicRates (Data exists)")
        return
    
    logger.info("Seeding ProductBasicRates...")
    
    prod_map = get_product_map(conn)
    # Map occupancy iib_code to id? We need occupancy_id. 
    # For sample data we know the iib_code keys 101, 201, 301 from seed_occupancies.
    # We should fetch current occupancies.
    occ_map_q = select(Occupancy.iib_code, Occupancy.id)
    occ_rows = conn.execute(occ_map_q).fetchall()
    occ_map = {row[0]: row[1] for row in occ_rows}
    
    if not occ_map:
        logger.warning("No occupancies found, cannot seed rates.")
        return

    csv_path = "data/product_basic_rates.csv"
    data = []
    
    if os.path.exists(csv_path):
         with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
            # Must convert product_code to id and iib_code to occupancy_id
    else:
        # Sample
        # Ensure we have codes '101' '201' '301' in occ_map
        residential_id = occ_map.get("101")
        office_id = occ_map.get("201")
        
        # Fallback if specific codes missing?
        first_occ_id = list(occ_map.values())[0] if occ_map else None
        
        data = []
        if residential_id and "BGRP" in prod_map:
            data.append({"product_code": "BGRP", "product_id": prod_map["BGRP"], "occupancy_id": residential_id, "basic_rate": 0.15})
        if office_id and "BSUSP" in prod_map:
            data.append({"product_code": "BSUSP", "product_id": prod_map["BSUSP"], "occupancy_id": office_id, "basic_rate": 0.20})

    for row in data:
        # If loading from CSV, we might need to resolve IDs. Assuming CSV has codes.
        # Minimal Logic for CSV resolution:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'occupancy_id' not in row and 'iib_code' in row:
             row['occupancy_id'] = occ_map.get(row['iib_code'])
             del row['iib_code'] # remove if model doesn't accept
        
        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(ProductBasicRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)


def seed_bsus_rates(conn):
    if table_has_rows(conn, "bsus_rates"):
        logger.info("Skipping BsusRates (Data exists)")
        return
        
    logger.info("Seeding BsusRates...")
    prod_map = get_product_map(conn)
    
    csv_path = "data/bsus_rates.csv"
    data = []
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
    else:
        if "BSUSP" in prod_map:
            data.append({
                "product_code": "BSUSP", 
                "product_id": prod_map["BSUSP"], 
                "occupancy_type": "Non-Industrial", 
                "eq_zone": "Zone I", 
                "basic_rate": 0.25
            })

    for row in data:
        if 'product_id' not in row and 'product_code' in row:
            row['product_id'] = prod_map.get(row['product_code'])
            
        if row.get('product_id'):
            stmt = pg_insert(BsusRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)

def seed_stfi_rates(conn):
    if table_has_rows(conn, "stfi_rates"): return
    logger.info("Seeding STFI Rates...")
    prod_map = get_product_map(conn)
    occ_map_q = select(Occupancy.iib_code, Occupancy.id)
    occ_rows = conn.execute(occ_map_q).fetchall()
    occ_map = {row[0]: row[1] for row in occ_rows}
    
    csv_path = "data/stfi_rates.csv"
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
    else:
        # Sample
        res_id = occ_map.get("101")
        if res_id and "BGRP" in prod_map:
            data.append({
                "product_code": "BGRP", 
                "product_id": prod_map["BGRP"], 
                "occupancy_id": res_id, 
                "stfi_rate": 0.05
            })
            
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'occupancy_id' not in row and 'iib_code' in row:
             row['occupancy_id'] = occ_map.get(row['iib_code'])
             del row['iib_code']
             
        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(StfiRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)

def seed_eq_rates(conn):
    if table_has_rows(conn, "eq_rates"): return
    logger.info("Seeding EQ Rates...")
    prod_map = get_product_map(conn)
    occ_map_q = select(Occupancy.iib_code, Occupancy.id)
    occ_rows = conn.execute(occ_map_q).fetchall()
    occ_map = {row[0]: row[1] for row in occ_rows}
    
    csv_path = "data/eq_rates.csv"
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
             reader = csv.DictReader(f)
             data = [row for row in reader]
    else:
        res_id = occ_map.get("101")
        if res_id and "BGRP" in prod_map:
            data.append({
                "product_code": "BGRP", 
                "product_id": prod_map["BGRP"], 
                "occupancy_id": res_id, 
                "eq_zone": "Zone I",
                "eq_rate": 0.10
            })
    
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'occupancy_id' not in row and 'iib_code' in row:
             row['occupancy_id'] = occ_map.get(row['iib_code'])
             del row['iib_code']

        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(EqRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)

def seed_terrorism_slabs(conn):
    # This must populate REAL values and handle the logic
    # We will use upsert safely or empty check
    if table_has_rows(conn, "terrorism_slabs"): 
        logger.info("Skipping TerrorismSlabs (Data exists)")
        return
    logger.info("Seeding TerrorismSlabs (Official Circular Values)...")
    prod_map = get_product_map(conn)
    
    # Official / Standard Pool Rates
    # Note: si_max of None can represent Infinity
    slabs = [
        # Residential: 0.10 per mille flat
        {"occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        # Non-Industrial: 0-2000Cr -> 0.12? Let's use 0.15 for safety/standard
        {"occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        # Non-Industrial: >20000Cr -> 0.12
        {"occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
        # Industrial: 0-2000Cr -> 0.20
        {"occupancy_type": "Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.20},
        # Industrial: >2000Cr -> 0.15
        {"occupancy_type": "Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.15},
    ]

    # Insert for ALL applicable products? Or generic?
    # The table has product_code.
    # We should insert these slab rows for every Fire product that uses Slab logic.
    # Typically SFSP, IAR. 
    # BGRP usually has flat rate but can share structure.
    # Let's add them for all loaded Fire products to be safe.
    
    fire_products = ["SFSP", "IAR", "BSUSP", "BLUSP"] # BGRP is usually handled separately but we can add
    
    for code in fire_products:
        pid = prod_map.get(code)
        if pid:
            for slab in slabs:
                row = slab.copy()
                row["product_code"] = code
                row["product_id"] = pid
                stmt = pg_insert(TerrorismSlab).values(**row).on_conflict_do_nothing()
                conn.execute(stmt)

def seed_add_on_master(conn):
    if table_has_rows(conn, "add_on_master"): return
    logger.info("Seeding AddOnMaster...")
    csv_path = "data/add_on_master.csv"
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
             reader = csv.DictReader(f)
             data = [row for row in reader]
    else:
        data = [
            {"add_on_code": "EARTHQUAKE", "add_on_name": "Earthquake (Fire and Shock)", "is_percentage": True},
            {"add_on_code": "STFI", "add_on_name": "Storm, Tempest, Flood, Inundation", "is_percentage": True},
            {"add_on_code": "TERRORISM", "add_on_name": "Terrorism Cover", "is_percentage": True}
        ]
    
    for row in data:
         stmt = pg_insert(AddOnMaster).values(**row).on_conflict_do_nothing()
         conn.execute(stmt)

def seed_add_on_product_map(conn):
    if table_has_rows(conn, "add_on_product_map"): return
    logger.info("Seeding AddOnProductMap...")
    
    prod_map = get_product_map(conn)
    # Get AddOn IDs
    ao_q = select(AddOnMaster.add_on_code, AddOnMaster.id)
    ao_rows = conn.execute(ao_q).fetchall()
    ao_map = {row[0]: row[1] for row in ao_rows}
    
    csv_path = "data/add_on_product_map.csv"
    data = []
    if os.path.exists(csv_path):
         with open(csv_path, 'r') as f:
             reader = csv.DictReader(f)
             data = [row for row in reader]
    else:
        # Sample: Link EQ to SFSP
        pid = prod_map.get("SFSP")
        aid = ao_map.get("EARTHQUAKE")
        if pid and aid:
            data.append({"add_on_id": aid, "product_code": "SFSP", "product_id": pid})
            
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'add_on_id' not in row and 'add_on_code' in row:
             row['add_on_id'] = ao_map.get(row['add_on_code'])
             del row['add_on_code']
             
        if row.get('product_id') and row.get('add_on_id'):
            stmt = pg_insert(AddOnProductMap).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)

def seed_add_on_rates(conn):
    if table_has_rows(conn, "add_on_rates"): return
    logger.info("Seeding AddOnRates...")
    
    prod_map = get_product_map(conn)
    ao_q = select(AddOnMaster.add_on_code, AddOnMaster.id)
    ao_rows = conn.execute(ao_q).fetchall()
    ao_map = {row[0]: row[1] for row in ao_rows}
    
    csv_path = "data/add_on_rates.csv"
    data = []
    if os.path.exists(csv_path):
         with open(csv_path, 'r') as f:
             reader = csv.DictReader(f)
             data = [row for row in reader]
    else:
         # Sample
         pid = prod_map.get("SFSP")
         aid = ao_map.get("EARTHQUAKE")
         if pid and aid:
            data.append({
                "product_code": "SFSP",
                "product_id": pid,
                "add_on_id": aid,
                "occupancy_type": "Residential",
                "rate_type": "per_mille",
                "rate_value": 0.10
            })
            
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'add_on_id' not in row and 'add_on_code' in row:
             row['add_on_id'] = ao_map.get(row['add_on_code'])
             del row['add_on_code']
        
        if row.get('product_id') and row.get('add_on_id'):
            stmt = pg_insert(AddOnRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)


def main():
    logger.info("Starting Seeding Process...")
    # Wrap in transaction
    conn = engine.connect()
    trans = conn.begin()
    
    try:
        seed_lob_and_product(conn) # Ensure masters exist first
        seed_occupancies(conn)
        seed_product_basic_rates(conn)
        seed_bsus_rates(conn)
        seed_stfi_rates(conn)
        seed_eq_rates(conn)
        seed_terrorism_slabs(conn)
        seed_add_on_master(conn)
        seed_add_on_product_map(conn)
        seed_add_on_rates(conn)
        
        trans.commit()
        logger.info("✅ Seeding Completed Successfully.")
    except Exception as e:
        logger.error(f"❌ Seeding Failed: {e}")
        trans.rollback()
        sys.exit(2)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
