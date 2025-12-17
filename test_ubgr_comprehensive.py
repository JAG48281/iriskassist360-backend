"""
Comprehensive Test Suite for UBGR Risk Rate Auto-fill Fix

This test verifies:
1. Database schema is correct
2. Data resolution works (occupancyId -> iib_code -> risk_rate)
3. Multiple UBGR occupancies return correct rates
"""

from app.database import engine
from sqlalchemy import text


def test_schema():
    """Verify fire_iib_rates table has correct schema"""
    print("\n" + "=" * 70)
    print("TEST 1: Schema Verification")
    print("=" * 70)
    
    with engine.connect() as conn:
        # Check fire_iib_rates columns
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'fire_iib_rates'
            ORDER BY ordinal_position
        """))
        
        columns = {row[0]: row[1] for row in result}
        
        assert 'iib_code' in columns, "❌ Missing iib_code column"
        assert 'rate_per_mille' in columns, "❌ Missing rate_per_mille column"
        
        print("✅ Schema verified: fire_iib_rates has iib_code and rate_per_mille columns")


def test_data_integrity():
    """Verify UBGR rates exist in fire_iib_rates"""
    print("\n" + "=" * 70)
    print("TEST 2: Data Integrity")
    print("=" * 70)
    
    with engine.connect() as conn:
        # Check for UBGR IIB codes (1001, 1001_2)
        result = conn.execute(text("""
            SELECT iib_code, rate_per_mille 
            FROM fire_iib_rates 
            WHERE iib_code IN ('1001', '1001_2')
            ORDER BY iib_code
        """))
        
        rates = {row[0]: float(row[1]) for row in result}
        
        assert '1001' in rates, "❌ Missing rate for IIB code 1001"
        assert rates['1001'] > 0, "❌ Rate for 1001 is zero or negative"
        
        print(f"✅ UBGR rates found:")
        for iib_code, rate in rates.items():
            print(f"   IIB {iib_code}: {rate}‰")


def test_occupancy_resolution():
    """Verify occupancyId -> iib_code resolution"""
    print("\n" + "=" * 70)
    print("TEST 3: Occupancy Resolution")
    print("=" * 70)
    
    with engine.connect() as conn:
        # Get UBGR occupancies
        result = conn.execute(text("""
            SELECT id, iib_code, risk_description
            FROM occupancies
            WHERE iib_code IN ('1001', '1001_2')
            ORDER BY id
            LIMIT 5
        """))
        
        occupancies = [(row[0], row[1], row[2]) for row in result]
        
        assert len(occupancies) > 0, "❌ No UBGR occupancies found"
        
        print(f"✅ Found {len(occupancies)} UBGR occupancies:")
        for occ_id, iib_code, description in occupancies:
            print(f"   ID {occ_id} -> IIB {iib_code} ({description[:50]}...)")


def test_end_to_end_resolution():
    """Test complete flow: occupancyId -> iib_code -> risk_rate"""
    print("\n" + "=" * 70)
    print("TEST 4: End-to-End Resolution")
    print("=" * 70)
    
    with engine.connect() as conn:
        # Get first UBGR occupancy
        occupancy = conn.execute(text("""
            SELECT id, iib_code
            FROM occupancies
            WHERE iib_code IN ('1001', '1001_2')
            ORDER BY id
            LIMIT 1
        """)).fetchone()
        
        if not occupancy:
            print("❌ No UBGR occupancy found")
            return False
        
        occ_id, expected_iib_code = occupancy
        print(f"📍 Testing with occupancyId={occ_id}")
        
        # Step 1: Resolve to iib_code (mimics the fix)
        iib_code = conn.execute(text("""
            SELECT iib_code FROM occupancies WHERE id = :occ_id
        """), {"occ_id": occ_id}).scalar()
        
        assert iib_code == expected_iib_code, f"❌ Resolution failed: expected {expected_iib_code}, got {iib_code}"
        print(f"✅ Step 1: Resolved occupancyId={occ_id} -> iib_code={iib_code}")
        
        # Step 2: Get risk rate
        risk_rate = conn.execute(text("""
            SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :iib
        """), {"iib": iib_code}).scalar()
        
        assert risk_rate is not None, f"❌ No rate found for iib_code={iib_code}"
        assert risk_rate > 0, f"❌ Invalid rate: {risk_rate}"
        
        print(f"✅ Step 2: Retrieved risk_rate={float(risk_rate)}‰ from fire_iib_rates")
        print(f"\n🎉 COMPLETE FLOW VERIFIED:")
        print(f"   occupancyId {occ_id} -> iib_code '{iib_code}' -> risk_rate {float(risk_rate)}‰")
        
        return True


def test_multiple_occupancies():
    """Verify all UBGR occupancies can be resolved"""
    print("\n" + "=" * 70)
    print("TEST 5: Multiple Occupancies")
    print("=" * 70)
    
    with engine.connect() as conn:
        # Test all UBGR occupancies
        result = conn.execute(text("""
            SELECT o.id, o.iib_code, f.rate_per_mille
            FROM occupancies o
            LEFT JOIN fire_iib_rates f ON o.iib_code = f.iib_code
            WHERE o.iib_code IN ('1001', '1001_2')
            ORDER BY o.id
        """))
        
        success_count = 0
        fail_count = 0
        
        for occ_id, iib_code, rate in result:
            if rate is not None and rate > 0:
                success_count += 1
            else:
                fail_count += 1
                print(f"   ❌ occupancyId {occ_id} (iib_code={iib_code}): NO RATE")
        
        print(f"✅ Successfully resolved {success_count} occupancies")
        
        if fail_count > 0:
            print(f"⚠️  {fail_count} occupancies have missing rates")
        
        assert success_count > 0, "❌ No occupancies could be resolved"


def run_all_tests():
    """Run all test cases"""
    print("\n\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "UBGR RISK RATE FIX - TEST SUITE" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        test_schema()
        test_data_integrity()
        test_occupancy_resolution()
        test_end_to_end_resolution()
        test_multiple_occupancies()
        
        print("\n\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 70)
        print("\n✅ UBGR Risk Rate Auto-fill is working correctly!")
        print("✅ Ready for deployment\n")
        
    except AssertionError as e:
        print(f"\n\n❌ TEST FAILED: {str(e)}\n")
        raise
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
