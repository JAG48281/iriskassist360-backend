"""
Post-Deployment Verification Script

Verifies that ONLY canonical tables remain after cleanup migration.
Run this AFTER applying the cleanup migration.
"""
from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required canonical tables (must exist)
REQUIRED_TABLES = [
    "lob_master",
    "occupancies",
    "fire_iib_rates",
    "fire_bsus_rates",
    "fire_stfi_rates",
    "fire_eq_rates",
    "terrorism_slabs",
    "fire_add_on_master",
    "fire_add_on_rates",
    "alembic_version"
]

# Legacy tables (must NOT exist)
FORBIDDEN_TABLES = [
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

def verify_schema_cleanup():
    """
    Post-deployment verification of schema cleanup.
    """
    print("\n" + "="*70)
    print("POST-DEPLOYMENT SCHEMA VERIFICATION")
    print("="*70)
    
    all_passed = True
    
    with engine.connect() as conn:
        # Get all user tables
        query = text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename NOT LIKE 'spatial_%'
            ORDER BY tablename
        """)
        result = conn.execute(query)
        all_tables = [row[0] for row in result.fetchall()]
        
        print(f"\nAll tables in public schema ({len(all_tables)} total):")
        for table in all_tables:
            print(f"  - {table}")
        
        # Check required tables exist
        print("\n" + "-"*70)
        print("REQUIRED TABLES CHECK")
        print("-"*70)
        
        missing_required = []
        for table in REQUIRED_TABLES:
            if table in all_tables:
                # Get row count
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"✅ {table}: EXISTS ({count} rows)")
                except:
                    print(f"✅ {table}: EXISTS (could not count rows)")
            else:
                print(f"❌ {table}: MISSING")
                missing_required.append(table)
                all_passed = False
        
        # Check forbidden tables removed
        print("\n" + "-"*70)
        print("FORBIDDEN TABLES CHECK")
        print("-"*70)
        
        found_forbidden = []
        for table in FORBIDDEN_TABLES:
            if table in all_tables:
                print(f"❌ {table}: STILL EXISTS (should be dropped)")
                found_forbidden.append(table)
                all_passed = False
            else:
                print(f"✅ {table}: REMOVED")
        
        # Check for unexpected tables
        print("\n" + "-"*70)
        print("UNEXPECTED TABLES CHECK")
        print("-"*70)
        
        expected_tables = set(REQUIRED_TABLES + FORBIDDEN_TABLES)
        unexpected_tables = [t for t in all_tables if t not in expected_tables]
        
        if unexpected_tables:
            print(f"\nℹ️  Found {len(unexpected_tables)} unexpected table(s):")
            for table in unexpected_tables:
                print(f"   - {table}")
            print("   (These may be application tables like users, quotes, etc.)")
        else:
            print("\nℹ️  No unexpected tables found")
        
        # Final summary
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        
        if all_passed:
            print("\n✅ ✅ ✅ SCHEMA CLEANUP VERIFIED ✅ ✅ ✅")
            print(f"\n✅ All {len(REQUIRED_TABLES)} required tables present")
            print(f"✅ All {len(FORBIDDEN_TABLES)} legacy tables removed")
            print("✅ Database schema is clean and canonical")
        else:
            print("\n❌ SCHEMA VERIFICATION FAILED")
            if missing_required:
                print(f"\n❌ Missing required tables: {missing_required}")
            if found_forbidden:
                print(f"❌ Forbidden tables still exist: {found_forbidden}")
        
        print("="*70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    is_verified = verify_schema_cleanup()
    exit(0 if is_verified else 1)
