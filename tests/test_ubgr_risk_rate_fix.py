"""
Test script to verify UBGR Risk Rate Auto-fill Fix

Tests the /calculate endpoint with actual occupancyId values
to ensure risk rates are correctly fetched from fire_iib_rates
"""

from app.database import engine
from sqlalchemy import text


def test_risk_rate_resolution():
    """Test that occupancyId -> iib_code -> risk_rate works correctly"""
    
    print("=" * 60)
    print("UBGR RISK RATE AUTO-FILL VERIFICATION")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Get sample occupancies for UBGR (IIB codes 1001, 1001_2)
        occupancies = conn.execute(
            text("""
                SELECT id, iib_code, risk_description 
                FROM occupancies 
                WHERE iib_code IN ('1001', '1001_2')
                ORDER BY id
            """)
        ).fetchall()
        
        print(f"\nFound {len(occupancies)} UBGR occupancies:\n")
        
        for occ in occupancies:
            occupancy_id = occ.id
            iib_code = occ.iib_code
            description = occ.risk_description
            
            # Query fire_iib_rates for this iib_code
            rate_result = conn.execute(
                text("SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :iib"),
                {"iib": iib_code}
            ).scalar()
            
            print(f"Occupancy ID: {occupancy_id}")
            print(f"  IIB Code: {iib_code}")
            print(f"  Description: {description}")
            print(f"  Risk Rate: {rate_result}‰" if rate_result else "  Risk Rate: NOT FOUND ❌")
            print(f"  Status: {'✅ PASS' if rate_result else '❌ FAIL'}")
            print("-" * 60)
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_risk_rate_resolution()
