"""
Schema Pre-Flight Auto-Check Module

Validates database schema before seeding and app startup.
Uses PostgreSQL system catalog for non-invasive schema verification.

AUTHORITATIVE: Products are LOGICAL, not relational.
NO product_master table exists or should exist.
"""
import logging
from typing import Dict, List, Tuple
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine

logger = logging.getLogger(__name__)

# Canonical tables that MUST exist for backend to function
REQUIRED_TABLES = [
    "lob_master",
    "occupancies",
    "fire_iib_rates",
    "fire_bsus_rates", 
    "fire_stfi_rates",
    "fire_eq_rates",
    "fire_terrorism_rates",
    "fire_add_on_master",
    "fire_add_on_rates",
    "alembic_version"
]

# Optional tables that are nice to have but not critical
OPTIONAL_TABLES = []

# Legacy/forbidden tables that should be ignored or removed
FORBIDDEN_TABLES = [
    "eq_rates",
    "bsus_rates",
    "stfi_rates",
    "generic_rates",
    "terrorism_slabs",  # Replaced by fire_terrorism_rates
    "product_master"  # NEVER should exist
]


def check_table_exists(conn, table_name: str) -> bool:
    """
    Check if table exists using PostgreSQL system catalog.
    Uses to_regclass() for efficient, non-invasive check.
    
    Returns: True if table exists, False otherwise
    """
    try:
        result = conn.execute(text(f"SELECT to_regclass('public.{table_name}')"))
        exists = result.scalar() is not None
        return exists
    except SQLAlchemyError as e:
        logger.warning(f"Could not check existence of {table_name}: {e}")
        return False


def get_all_user_tables(conn) -> List[str]:
    """
    Get list of all user-created tables in public schema.
    Excludes system tables and PostGIS tables.
    """
    try:
        query = text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename NOT LIKE 'spatial_%'
            ORDER BY tablename
        """)
        result = conn.execute(query)
        return [row[0] for row in result.fetchall()]
    except SQLAlchemyError as e:
        logger.warning(f"Could not retrieve table list: {e}")
        return []


def categorize_tables(conn) -> Dict[str, List[str]]:
    """
    Categorize all tables into: present, missing, unexpected, forbidden.
    
    Returns:
        {
            "present": [...],      # Required tables that exist
            "missing": [...],      # Required tables that don't exist
            "optional": [...],     # Optional tables that exist
            "unexpected": [...],   # Tables not in any category
            "forbidden": [...]     # Legacy/forbidden tables that exist
        }
    """
    categories = {
        "present": [],
        "missing": [],
        "optional": [],
        "unexpected": [],
        "forbidden": []
    }
    
    # Check required tables
    for table in REQUIRED_TABLES:
        if check_table_exists(conn, table):
            categories["present"].append(table)
        else:
            categories["missing"].append(table)
    
    # Check optional tables
    for table in OPTIONAL_TABLES:
        if check_table_exists(conn, table):
            categories["optional"].append(table)
    
    # Check forbidden tables
    for table in FORBIDDEN_TABLES:
        if check_table_exists(conn, table):
            categories["forbidden"].append(table)
    
    # Find unexpected tables
    all_tables = get_all_user_tables(conn)
    known_tables = set(REQUIRED_TABLES + OPTIONAL_TABLES + FORBIDDEN_TABLES)
    
    for table in all_tables:
        if table not in known_tables and table not in categories["present"] and table not in categories["forbidden"]:
            categories["unexpected"].append(table)
    
    return categories


def print_schema_report(categories: Dict[str, List[str]]) -> None:
    """
    Print a clean, readable schema validation report.
    """
    print("\n" + "="*70)
    print("SCHEMA PRE-FLIGHT CHECK")
    print("="*70)
    
    # Present tables (required)
    if categories["present"]:
        print(f"\n✅ PRESENT ({len(categories['present'])}/{len(REQUIRED_TABLES)} required):")
        for table in sorted(categories["present"]):
            print(f"   ✅ {table}")
    
    # Missing tables (ERROR)
    if categories["missing"]:
        print(f"\n❌ MISSING ({len(categories['missing'])} required tables):")
        for table in sorted(categories["missing"]):
            print(f"   ❌ {table} - REQUIRED but not found")
            logger.error(f"Required table missing: {table}")
    
    # Optional tables
    if categories["optional"]:
        print(f"\nℹ️  OPTIONAL ({len(categories['optional'])} present):")
        for table in sorted(categories["optional"]):
            print(f"   ℹ️  {table}")
    
    # Forbidden tables (WARNING)
    if categories["forbidden"]:
        print(f"\n⚠️  FORBIDDEN ({len(categories['forbidden'])} legacy/forbidden tables):")
        for table in sorted(categories["forbidden"]):
            if table == "product_master":
                print(f"   ❌ {table} - CRITICAL: Should NEVER exist!")
                logger.critical(f"FORBIDDEN table exists: {table} (products are LOGICAL, not relational)")
            else:
                print(f"   ⚠️  {table} - Legacy table (should be removed)")
                logger.warning(f"Legacy table exists: {table}")
    
    # Unexpected tables (INFO)
    if categories["unexpected"]:
        print(f"\nℹ️  UNEXPECTED ({len(categories['unexpected'])} unknown tables):")
        for table in sorted(categories["unexpected"]):
            print(f"   ℹ️  {table}")
            logger.info(f"Unexpected table found: {table}")
    
    # Summary
    print("\n" + "-"*70)
    total_required = len(REQUIRED_TABLES)
    total_present = len(categories["present"])
    total_missing = len(categories["missing"])
    
    if total_missing == 0:
        print(f"✅ Schema Status: HEALTHY ({total_present}/{total_required} required tables present)")
    else:
        print(f"⚠️  Schema Status: INCOMPLETE ({total_present}/{total_required} required tables present)")
        print(f"   Missing {total_missing} required table(s)")
    
    if "product_master" in categories["forbidden"]:
        print("❌ CRITICAL: product_master table exists - FORBIDDEN!")
    
    print("="*70 + "\n")


def run_schema_preflight() -> Tuple[bool, Dict[str, List[str]]]:
    """
    Run complete schema pre-flight check.
    
    Returns:
        (is_healthy, categories)
        is_healthy: True if all required tables present
        categories: Categorized tables dict
    """
    logger.info("Running schema pre-flight check...")
    
    try:
        with engine.connect() as conn:
            categories = categorize_tables(conn)
            print_schema_report(categories)
            
            # Determine health status
            is_healthy = len(categories["missing"]) == 0
            
            # CRITICAL: Check for forbidden product_master
            if "product_master" in categories["forbidden"]:
                logger.critical("FATAL: product_master table exists - products are LOGICAL, not relational!")
                is_healthy = False
            
            return is_healthy, categories
            
    except Exception as e:
        logger.error(f"Schema pre-flight check failed: {e}")
        print(f"\n❌ Schema pre-flight check failed: {e}\n")
        return False, {
            "present": [],
            "missing": REQUIRED_TABLES,
            "optional": [],
            "unexpected": [],
            "forbidden": []
        }


def get_schema_status() -> Dict[str, any]:
    """
    Get schema status for health endpoint.
    Non-invasive, safe for production monitoring.
    
    Returns:
        {
            "required_tables_present": bool,
            "missing_tables": [...],
            "forbidden_tables": [...],
            "unexpected_tables": [...],
            "total_required": int,
            "total_present": int
        }
    """
    try:
        with engine.connect() as conn:
            categories = categorize_tables(conn)
            
            return {
                "required_tables_present": len(categories["missing"]) == 0,
                "missing_tables": categories["missing"],
                "forbidden_tables": categories["forbidden"],
                "unexpected_tables": categories["unexpected"],
                "total_required": len(REQUIRED_TABLES),
                "total_present": len(categories["present"])
            }
    except Exception as e:
        logger.error(f"Could not get schema status: {e}")
        return {
            "required_tables_present": False,
            "missing_tables": REQUIRED_TABLES,
            "forbidden_tables": [],
            "unexpected_tables": [],
            "total_required": len(REQUIRED_TABLES),
            "total_present": 0
        }


if __name__ == "__main__":
    # Allow running as standalone checker
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    is_healthy, categories = run_schema_preflight()
    
    if is_healthy:
        print("✅ Schema is healthy - all required tables present")
        exit(0)
    else:
        print("❌ Schema has issues - see report above")
        exit(1)
