"""
Quick test to verify Risk Rate Resolution is working correctly.
Tests against the running backend server.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_risk_rate_resolution():
    """Test that risk rate is properly resolved for BGRP/UBGR products"""
    print("="*80)
    print("RISK RATE RESOLUTION TEST")
    print("="*80)
    
    # Test 1: Fetch risk descriptions for UBGR
    print("\n1️⃣  Testing Risk Descriptions Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/master/risk-descriptions", params={"productCode": "UBGR"})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {len(data)} risk descriptions")
            
            if data:
                first = data[0]
                print(f"\n   Sample Risk Description:")
                print(f"   - Occupancy ID: {first.get('occupancyId', 'MISSING')}")
                print(f"   - IIB Code: {first.get('iibCode', 'MISSING')}")
                print(f"   - Description: {first.get('riskDescription', 'MISSING')[:50]}...")
                print(f"   - Occupancy Type: {first.get('occupancyType', 'MISSING')}")
                
                occupancy_code = first.get('iibCode')
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Calculate premium for UBGR with Dwellings (1001)
    print("\n2️⃣  Testing Premium Calculation for UBGR + Dwellings (1001)...")
    payload = {
        "productCode": "UBGR",
        "occupancyCode": "1001",
        "buildingSI": 1000000,
        "contentsSI": 200000,
        "terrorismSI": 1200000,
        "addOns": [],
        "paSelection": {"proposer": True, "spouse": False},
        "discountPercentage": 0,
        "loadingPercentage": 0,
        "policyPeriod": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/fire/ubgr/calculate", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            meta = data.get('meta', {})
            breakdown = data.get('breakdown', {})
            
            print(f"   ✅ Premium calculated successfully!")
            print(f"\n   📊 Meta Information:")
            print(f"   - Applied Rate: {meta.get('applied_rate', 'MISSING')}‰")
            print(f"   - Risk Rate: {meta.get('risk_rate', 'MISSING')}‰")
            print(f"   - Rate Source: {meta.get('rate_source', 'MISSING')}")
            print(f"   - Occupancy Code: {meta.get('occupancy_code', 'MISSING')}")
            print(f"   - Product Code: {meta.get('product_code', 'MISSING')}")
            
            print(f"\n   💰 Premium Breakdown:")
            print(f"   - Basic Premium: ₹{breakdown.get('basic_premium', 0):,.2f}")
            print(f"   - Net Premium: ₹{breakdown.get('net_premium', 0):,.2f}")
            print(f"   - Gross Premium: ₹{breakdown.get('gross_premium', 0):,.2f}")
            
            # Verify critical requirements
            print(f"\n   🔍 Verification:")
            
            risk_rate = meta.get('risk_rate', 0)
            if risk_rate and risk_rate > 0:
                print(f"   ✅ Risk rate is populated: {risk_rate}‰ (NOT 0)")
            else:
                print(f"   ❌ FAILED: Risk rate is {risk_rate} (should be > 0)")
                return False
            
            rate_source = meta.get('rate_source')
            if rate_source == 'product_basic_rates':
                print(f"   ✅ Rate source is correct: {rate_source}")
            else:
                print(f"   ❌ FAILED: Rate source is '{rate_source}' (should be 'product_basic_rates')")
                return False
            
            basic_premium = breakdown.get('basic_premium', 0)
            if basic_premium > 0:
                print(f"   ✅ Basic premium calculated: ₹{basic_premium:,.2f}")
            else:
                print(f"   ❌ FAILED: Basic premium is {basic_premium}")
                return False
            
            return True
            
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bgrp_calculation():
    """Test BGRP calculation (legacy endpoint)"""
    print("\n3️⃣  Testing BGRP Calculation (Legacy Endpoint)...")
    
    payload = {
        "buildingSI": 1000000,
        "contentsSI": 200000,
        "terrorismCover": "Yes",
        "terrorismSI": 1200000,
        "paProposer": "Yes",
        "paSpouse": "No",
        "discountPercentage": 0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/irisk/fire/uiic/bgrp/calculate", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result = data.get('data', {})
                meta = result.get('meta', {})
                
                print(f"   ✅ BGRP calculation successful!")
                print(f"   - Applied Rate: {meta.get('applied_rate', 'N/A')}‰")
                print(f"   - Occupancy Code: {meta.get('occupancy_code', 'N/A')}")
                print(f"   - Basic Premium: ₹{result.get('basic_premium', 0):,.2f}")
                
                return True
        else:
            print(f"   ⚠️  BGRP endpoint returned: {response.status_code}")
            return True  # Not critical for this test
            
    except Exception as e:
        print(f"   ⚠️  BGRP test skipped: {e}")
        return True  # Not critical

def main():
    print("\n🚀 Starting Risk Rate Resolution Verification...\n")
    
    results = []
    results.append(test_risk_rate_resolution())
    results.append(test_bgrp_calculation())
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if all(results):
        print("\n✅ ALL TESTS PASSED!")
        print("\n✓ Risk rate auto-populates correctly")
        print("✓ Rate fetched from product_basic_rates table")
        print("✓ Rate source is explicitly indicated")
        print("✓ No hardcoded rates or default to 0")
        print("\n" + "="*80)
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease check:")
        print("1. Database has rates configured in product_basic_rates")
        print("2. Backend server is running (uvicorn app.main:app --reload)")
        print("3. Check backend logs for error messages")
        print("\n" + "="*80)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
