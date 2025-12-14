"""
API Test Script - Risk Rate Resolution
Tests the complete flow from risk description selection to premium calculation.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_risk_descriptions():
    """Test 1: Fetch risk descriptions for UBGR"""
    print("\n" + "="*80)
    print("TEST 1: Fetch Risk Descriptions for UBGR")
    print("="*80)
    
    url = f"{BASE_URL}/master/risk-descriptions"
    params = {"productCode": "UBGR"}
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} risk descriptions")
            
            # Check first item
            if data:
                first = data[0]
                print(f"\nSample Risk Description:")
                print(f"  - Occupancy ID: {first.get('occupancyId', 'MISSING')}")
                print(f"  - IIB Code: {first.get('iibCode', 'MISSING')}")
                print(f"  - Description: {first.get('riskDescription', 'MISSING')}")
                print(f"  - Occupancy Type: {first.get('occupancyType', 'MISSING')}")
                print(f"  - AIFT Section: {first.get('aiftSection', 'MISSING')}")
                
                # Verify all required fields are present
                required = ['occupancyId', 'iibCode', 'riskDescription', 'occupancyType', 'aiftSection']
                missing = [f for f in required if f not in first]
                
                if missing:
                    print(f"\n❌ MISSING FIELDS: {missing}")
                else:
                    print(f"\n✅ All required fields present")
                    
                return first.get('iibCode')  # Return for next test
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_premium_calculation(occupancy_code="1001"):
    """Test 2: Calculate premium for UBGR"""
    print("\n" + "="*80)
    print(f"TEST 2: Calculate UBGR Premium (Occupancy: {occupancy_code})")
    print("="*80)
    
    url = f"{BASE_URL}/fire/ubgr/calculate"
    payload = {
        "productCode": "UBGR",
        "occupancyCode": occupancy_code,
        "buildingSI": 1000000,
        "contentsSI": 200000,
        "terrorismSI": 1200000,
        "addOns": [],
        "paSelection": {
            "proposer": True,
            "spouse": False
        },
        "discountPercentage": 0,
        "loadingPercentage": 0,
        "policyPeriod": 1
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            
            # Check meta fields
            meta = data.get('meta', {})
            print(f"\nMeta Information:")
            print(f"  - Applied Rate: {meta.get('applied_rate', 'MISSING')}‰")
            print(f"  - Risk Rate: {meta.get('risk_rate', 'MISSING')}‰")
            print(f"  - Rate Source: {meta.get('rate_source', 'MISSING')}")
            print(f"  - Terrorism Rate: {meta.get('terrorism_rate', 'MISSING')}‰")
            print(f"  - Occupancy Code: {meta.get('occupancy_code', 'MISSING')}")
            print(f"  - Product Code: {meta.get('product_code', 'MISSING')}")
            
            # Check breakdown
            breakdown = data.get('breakdown', {})
            print(f"\nPremium Breakdown:")
            print(f"  - Basic Premium: ₹{breakdown.get('basic_premium', 0):,.2f}")
            print(f"  - Terrorism Premium: ₹{breakdown.get('terrorism_premium', 0):,.2f}")
            print(f"  - Net Premium: ₹{breakdown.get('net_premium', 0):,.2f}")
            print(f"  - Gross Premium: ₹{breakdown.get('gross_premium', 0):,.2f}")
            
            # Verify critical fields
            if meta.get('risk_rate') and meta.get('risk_rate') > 0:
                print(f"\n✅ Risk rate is populated: {meta.get('risk_rate')}‰")
            else:
                print(f"\n❌ Risk rate is 0 or missing!")
                
            if meta.get('rate_source') == 'product_basic_rates':
                print(f"✅ Rate source is correct: {meta.get('rate_source')}")
            else:
                print(f"❌ Rate source is incorrect: {meta.get('rate_source')}")
                
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_missing_rate():
    """Test 3: Test error handling for missing rate"""
    print("\n" + "="*80)
    print("TEST 3: Test Error Handling (Invalid Occupancy)")
    print("="*80)
    
    url = f"{BASE_URL}/fire/ubgr/calculate"
    payload = {
        "productCode": "UBGR",
        "occupancyCode": "9999",  # Invalid occupancy
        "buildingSI": 1000000,
        "contentsSI": 0,
        "terrorismSI": 1000000,
        "addOns": [],
        "paSelection": {"proposer": False, "spouse": False},
        "discountPercentage": 0,
        "loadingPercentage": 0,
        "policyPeriod": 1
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            error = response.json()
            print(f"✅ Correctly returned 400 error")
            print(f"Error message: {error.get('detail', 'No detail')}")
            
            # Check if error message is explicit
            detail = str(error.get('detail', ''))
            if 'not configured' in detail.lower():
                print(f"✅ Error message is explicit and helpful")
            else:
                print(f"⚠️ Error message could be more explicit")
        else:
            print(f"⚠️ Expected 400, got {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all API tests"""
    print("\n" + "="*80)
    print("API TEST SUITE - RISK RATE RESOLUTION")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    
    # Test 1: Fetch risk descriptions
    occupancy_code = test_risk_descriptions()
    
    # Test 2: Calculate premium
    if occupancy_code:
        test_premium_calculation(occupancy_code)
    else:
        test_premium_calculation("1001")  # Use default
    
    # Test 3: Test error handling
    test_missing_rate()
    
    print("\n" + "="*80)
    print("✅ API TESTS COMPLETED")
    print("="*80)
    print("\nNOTE: Make sure the backend server is running at", BASE_URL)
    print("Run: uvicorn app.main:app --reload")
    print("="*80)

if __name__ == "__main__":
    main()
