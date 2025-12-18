"""
Test script to validate terrorism rates auto-seeding.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.seed_terrorism_rates import seed_fire_terrorism_rates, TERRORISM_SEED_DATA
from app.database import engine
from sqlalchemy import text


def test_auto_seeding():
    """Test that auto-seeding works correctly"""
    
    print("\n" + "="*70)
    print("TERRORISM RATES AUTO-SEEDING TEST")
    print("="*70)
    
    try:
        # Clear the table first for testing
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text("DELETE FROM fire_terrorism_rates"))
                trans.commit()
                print("\n✓ Cleared fire_terrorism_rates table for testing")
            except:
                trans.rollback()
                raise
        
        # Test seeding
        print("\n--- First Seed (should insert data) ---")
        seed_fire_terrorism_rates(engine)
        
        # Verify data was inserted
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM fire_terrorism_rates"))
            count = result.scalar()
            print(f"\n✓ Table now has {count} rows (Expected: {len(TERRORISM_SEED_DATA)})")
            
            if count != len(TERRORISM_SEED_DATA):
                print(f"\n❌ FAIL: Expected {len(TERRORISM_SEED_DATA)} rows, got {count}")
                return False
        
        # Test idempotency
        print("\n--- Second Seed (should skip - idempotent) ---")
        seed_fire_terrorism_rates(engine)
        
        # Verify count didn't change
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM fire_terrorism_rates"))
            count_after = result.scalar()
            print(f"\n✓ Table still has {count_after} rows (no duplicates)")
            
            if count_after != count:
                print(f"\n❌ FAIL: Idempotency broken - count changed from {count} to {count_after}")
                return False
        
        # Verify data content
        print("\n--- Verifying Seed Data ---")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT occupancy_type, min_sum_insured, max_sum_insured, rate_per_mille
                FROM fire_terrorism_rates
                ORDER BY occupancy_type, min_sum_insured
            """))
            
            rows = result.fetchall()
            for row in rows:
                max_si = f"{row.max_sum_insured:,}" if row.max_sum_insured else "Unlimited"
                print(f"  ✓ {row.occupancy_type:15} | {row.min_sum_insured:15,} - {max_si:15} | {row.rate_per_mille} per mille")
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED - Auto-seeding works correctly!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_auto_seeding()
    sys.exit(0 if success else 1)
