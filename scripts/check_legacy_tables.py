"""
Safety Check: Verify row counts before dropping legacy tables

This script checks if legacy tables have data before dropping them.
Run this BEFORE applying the cleanup migration.
"""
from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy tables to check
LEGACY_TABLES = [
    "product_basic_rates",
    "product_master",
    "generic_rates",
    "add_on_master",
    "add_on_products",
    "add_on_rates",
    "stfi_rates",
    "bsus_rates",
    "eq_rates"
]

def check_legacy_table_counts():
    """
    Safety check: Count rows in legacy tables before dropping.
    """
    print("\n" + "="*70)
    print("LEGACY TABLE SAFETY CHECK")
    print("="*70)
    print("\nChecking row counts in tables to be dropped...\n")
    
    results = {}
    total_rows = 0
    
    with engine.connect() as conn:
        for table in LEGACY_TABLES:
            try:
                # Check if table exists
                exists = conn.execute(text(f"SELECT to_regclass('public.{table}')")).scalar()
                
                if exists:
                    # Table exists, count rows
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    results[table] = count
                    total_rows += count
                    
                    if count > 0:
                        logger.warning(f"⚠️  {table}: {count} rows (HAS DATA)")
                    else:
                        logger.info(f"✅ {table}: {count} rows (empty, safe to drop)")
                else:
                    results[table] = None
                    logger.info(f"ℹ️  {table}: Table does not exist")
                    
            except Exception as e:
                conn.rollback()
                results[table] = f"ERROR: {e}"
                logger.error(f"❌ {table}: Could not check - {e}")
    
    # Summary
    print("\n" + "-"*70)
    print("SUMMARY")
    print("-"*70)
    
    tables_with_data = [t for t, count in results.items() if isinstance(count, int) and count > 0]
    
    if tables_with_data:
        print(f"\n⚠️  WARNING: {len(tables_with_data)} table(s) have data:")
        for table in tables_with_data:
            print(f"   - {table}: {results[table]} rows")
        print(f"\nTotal rows to be lost: {total_rows}")
        print("\n⚠️  RECOMMENDATION: Migrate data before dropping if needed")
        print("=" * 70 + "\n")
        return False
    else:
        print("\n✅ All legacy tables are empty or don't exist")
        print("✅ Safe to proceed with cleanup migration")
        print("="*70 + "\n")
        return True

if __name__ == "__main__":
    is_safe = check_legacy_table_counts()
    exit(0 if is_safe else 1)
