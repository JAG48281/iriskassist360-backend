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

def get_occupancy_id_map(conn):
    """Fetch iib_code -> id map."""
    query = select(Occupancy.iib_code, Occupancy.id)
    result = conn.execute(query).fetchall()
    return {row[0]: row[1] for row in result}

def get_occupancy_type_map(conn):
    """Fetch iib_code -> occupancy_type map."""
    query = select(Occupancy.iib_code, Occupancy.occupancy_type)
    result = conn.execute(query).fetchall()
    return {row[0]: row[1] for row in result}

def seed_lob_and_product(conn):
    """Seed LobMaster and ProductMaster."""
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
    logger.info("Seeding ProductBasicRates...")
    
    prod_map = get_product_map(conn)
    occ_id_map = get_occupancy_id_map(conn)
    
    if not occ_id_map:
        logger.warning("No occupancies found, cannot seed rates.")
        return

    csv_path = "data/product_basic_rates.csv"
    data = []
    
    if os.path.exists(csv_path):
         with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
    else:
        # Sample using iib_code
        data = []
        if "BGRP" in prod_map:
            data.append({"product_code": "BGRP", "iib_code": "101", "basic_rate": 0.15})
        if "BSUSP" in prod_map:
            data.append({"product_code": "BSUSP", "iib_code": "201", "basic_rate": 0.20})

    for row in data:
        p_code = row.get("product_code")
        iib = row.get("iib_code")
        
        # Determine product_id
        if 'product_id' not in row:
             row['product_id'] = prod_map.get(p_code)

        # Determine occupancy_id from iib_code if present
        if 'occupancy_id' not in row and iib:
             row['occupancy_id'] = occ_id_map.get(iib)
             # Remove iib_code so it doesn't fail insert if model doesn't have it
             if 'iib_code' in row: del row['iib_code']
        
        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(ProductBasicRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)
        else:
            logger.warning(f"Skipping product_basic_rates row due to missing map: Product={p_code}, IIB={iib}")

def seed_bsus_rates(conn):
    logger.info("Seeding BsusRates...")
    prod_map = get_product_map(conn)
    occ_id_map = get_occupancy_id_map(conn)
    
    csv_path = "data/bsus_rates.csv"
    data = []
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
    else:
        if "BSUSP" in prod_map:
            # Use '201' for Non-Industrial for BSUS sample
            data.append({
                "product_code": "BSUSP", 
                "iib_code": "201", 
                "eq_zone": "Zone I", 
                "basic_rate": 0.25
            })

    for row in data:
        p_code = row.get("product_code")
        iib = row.get("iib_code")
        
        if 'product_id' not in row:
            row['product_id'] = prod_map.get(p_code)

        if 'occupancy_id' not in row and iib:
            row['occupancy_id'] = occ_id_map.get(iib)
            if 'iib_code' in row: del row['iib_code']
            
        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(BsusRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)
        else:
            logger.warning(f"Skipping bsus_rates row: Product={p_code}, IIB={iib}")

def seed_stfi_rates(conn):
    logger.info("Seeding STFI Rates...")
    prod_map = get_product_map(conn)
    occ_id_map = get_occupancy_id_map(conn)
    
    csv_path = "data/stfi_rates.csv"
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
    else:
        # Sample using iib_code
        data = []
        if "BGRP" in prod_map:
            data.append({
                "product_code": "BGRP", 
                "iib_code": "101",
                "stfi_rate": 0.05
            })
            
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        
        iib = row.get("iib_code")
        if 'occupancy_id' not in row and iib:
             row['occupancy_id'] = occ_id_map.get(iib)
             if 'iib_code' in row: del row['iib_code']
             
        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(StfiRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)
        else:
            logger.warning(f"Skipping stfi_rates row: Product={row.get('product_code')}, IIB={iib}")

def seed_eq_rates(conn):
    logger.info("Seeding EQ Rates...")
    prod_map = get_product_map(conn)
    occ_id_map = get_occupancy_id_map(conn)
    
    csv_path = "data/eq_rates.csv"
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
             reader = csv.DictReader(f)
             data = [row for row in reader]
    else:
        data = []
        if "BGRP" in prod_map:
            data.append({
                "product_code": "BGRP", 
                "iib_code": "101",
                "eq_zone": "Zone I",
                "eq_rate": 0.10
            })
    
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        
        iib = row.get("iib_code")
        if 'occupancy_id' not in row and iib:
             row['occupancy_id'] = occ_id_map.get(iib)
             if 'iib_code' in row: del row['iib_code']

        if row.get('product_id') and row.get('occupancy_id'):
            stmt = pg_insert(EqRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)
        else:
            logger.warning(f"Skipping eq_rates row: Product={row.get('product_code')}, IIB={iib}")

def seed_terrorism_slabs(conn):
    logger.info("Seeding TerrorismSlabs (Official Circular Values)...")
    prod_map = get_product_map(conn)
    
    slabs = [
        {"occupancy_type": "Residential", "si_min": 0, "si_max": None, "rate_per_mille": 0.10},
        {"occupancy_type": "Non-Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.15},
        {"occupancy_type": "Non-Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.12},
        {"occupancy_type": "Industrial", "si_min": 0, "si_max": 20000000000, "rate_per_mille": 0.20},
        {"occupancy_type": "Industrial", "si_min": 20000000000, "si_max": None, "rate_per_mille": 0.15},
    ]

    fire_products = ["SFSP", "IAR", "BSUSP", "BLUSP"] 
    
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
            data.append({"add_on_code": "EARTHQUAKE", "product_code": "SFSP"})
            
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'add_on_id' not in row and 'add_on_code' in row:
             row['add_on_id'] = ao_map.get(row['add_on_code'])
             del row['add_on_code'] # remove safe
             
        if row.get('product_id') and row.get('add_on_id'):
            stmt = pg_insert(AddOnProductMap).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)
        else:
            logger.warning(f"Skipping add_on_product_map row. PID={row.get('product_id')} AID={row.get('add_on_id')}")

def seed_add_on_rates(conn):
    logger.info("Seeding AddOnRates...")
    
    prod_map = get_product_map(conn)
    ao_q = select(AddOnMaster.add_on_code, AddOnMaster.id)
    ao_rows = conn.execute(ao_q).fetchall()
    ao_map = {row[0]: row[1] for row in ao_rows}
    occ_type_map = get_occupancy_type_map(conn)

    csv_path = "data/add_on_rates.csv"
    data = []
    if os.path.exists(csv_path):
         with open(csv_path, 'r') as f:
             reader = csv.DictReader(f)
             data = [row for row in reader]
    else:
         # Sample
         if "SFSP" in prod_map and "EARTHQUAKE" in ao_map:
            data.append({
                "product_code": "SFSP",
                "add_on_code": "EARTHQUAKE",
                "iib_code": "101", # Should resolve to Residential
                "rate_type": "per_mille",
                "rate_value": 0.10
            })
            
    for row in data:
        if 'product_id' not in row and 'product_code' in row:
             row['product_id'] = prod_map.get(row['product_code'])
        if 'add_on_id' not in row and 'add_on_code' in row:
             row['add_on_id'] = ao_map.get(row['add_on_code'])
             del row['add_on_code']
        
        iib = row.get("iib_code")
        if 'occupancy_type' not in row and iib:
             row['occupancy_type'] = occ_type_map.get(iib)
             if 'iib_code' in row: del row['iib_code']
        
        if row.get('product_id') and row.get('add_on_id'):
            stmt = pg_insert(AddOnRate).values(**row).on_conflict_do_nothing()
            conn.execute(stmt)
        else:
             logger.warning(f"Skipping add_on_rates row. PID={row.get('product_id')} AID={row.get('add_on_id')}")

def verify_seeding(conn):
    tables = ["lob_master", "product_master", "occupancies", "product_basic_rates", "bsus_rates", "stfi_rates", "eq_rates", "terrorism_slabs", "add_on_master", "add_on_product_map", "add_on_rates"]
    logger.info("--- Post-Seeding Validation ---")
    
    total_failure = False
    
    for t in tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            logger.info(f"Table {t}: {count} rows")
            
            if t == "lob_master" and count == 0:
                logger.error("CRITICAL: lob_master is empty! Seeding definitely failed.")
                total_failure = True
        except Exception as e:
            logger.error(f"Could not count {t}: {e}")

    if total_failure:
        raise Exception("Verification failed: Critical tables are empty.")

def main():
    print("🚀 SEEDING SCRIPT STARTING... (Standard Output)", flush=True)
    # Debug Info
    import os
    logger.info(f"Current Working Directory: {os.getcwd()}")
    
    data_dir = os.path.join(os.getcwd(), "data")
    if os.path.exists(data_dir):
        logger.info(f"Contents of {data_dir}: {os.listdir(data_dir)}")
    else:
        logger.warning(f"Data directory {data_dir} does NOT exist!")

    logger.info("Starting Seeding Process...")
    
    # Wrap in transaction
    conn = engine.connect()
    
    # Check what DB we are connected to
    try:
        db_name = conn.execute(text("SELECT current_database()")).scalar()
        logger.info(f"Connected to Database: {db_name}")
    except Exception as e:
        logger.error(f"DB Connection check failed: {e}")

    trans = conn.begin()
    
    try:
        seed_lob_and_product(conn)
        seed_occupancies(conn)
        seed_product_basic_rates(conn)
        seed_bsus_rates(conn)
        seed_stfi_rates(conn)
        seed_eq_rates(conn)
        seed_terrorism_slabs(conn)
        seed_add_on_master(conn)
        seed_add_on_product_map(conn)
        seed_add_on_rates(conn)
        
        verify_seeding(conn)

        trans.commit()
        logger.info("✅ Seeding Completed Successfully.")
    except Exception as e:
        logger.error(f"❌ Seeding Failed: {e}")
        import traceback
        traceback.print_exc()
        trans.rollback()
        sys.exit(2)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
