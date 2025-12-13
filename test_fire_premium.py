"""
Test script for UBGR/UVGR/UVGS premium calculation API.
Validates strict business rules and calculation flow.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_ubgr_basic():
    """Test UBGR with basic scenario"""
    print("\n" + "="*60)
    print("TEST 1: UBGR Basic Calculation")
    print("="*60)
    
    payload = {
        "productCode": "UBGR",
        "occupancyCode": "1001",
        "buildingSI": 1000000,
        "contentsSI": 200000,
        "addOns": [],
        "paSelection": {
            "proposer": False,
            "spouse": False
        },
        "discountPercentage": 0,
        "loadingPercentage": 0
    }
    
    response = requests.post(f"{BASE_URL}/api/fire/ubgr/calculate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        breakdown = data['breakdown']
        
        print(f"✅ Status: {response.status_code}")
        print(f"\nBreakdown:")
        print(f"  Total SI: {breakdown['totalSI']}")
        print(f"  Basic Fire Premium: {breakdown['basicFirePremium']}")
        print(f"  Add-On Premium: {breakdown['addOnPremium']}")
        print(f"  Discount Amount: {breakdown['discountAmount']}")
        print(f"  Subtotal: {breakdown['subtotal']}")
        print(f"  Loading Amount: {breakdown['loadingAmount']}")
        print(f"  Terrorism Premium: {breakdown['terrorismPremium']}")
        print(f"  Net Premium: {breakdown['netPremium']}")
        print(f"  CGST: {breakdown['cgst']}")
        print(f"  SGST: {breakdown['sgst']}")
        print(f"  Stamp Duty: {breakdown['stampDuty']}")
        print(f"  Gross Premium: {breakdown['grossPremium']}")
        
        # Validate calculation
        expected_subtotal = breakdown['basicFirePremium'] + breakdown['addOnPremium'] - breakdown['discountAmount']
        assert abs(breakdown['subtotal'] - expected_subtotal) < 0.01, "Subtotal mismatch"
        
        expected_net = breakdown['subtotal'] + breakdown['loadingAmount'] + breakdown['terrorismPremium']
        assert abs(breakdown['netPremium'] - expected_net) < 0.01, "Net Premium mismatch"
        
        print("\n✅ Calculation validated")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_ubgr_with_discount_loading():
    """Test UBGR with discount and loading"""
    print("\n" + "="*60)
    print("TEST 2: UBGR with Discount & Loading")
    print("="*60)
    
    payload = {
        "productCode": "UBGR",
        "occupancyCode": "1001",
        "buildingSI": 1000000,
        "contentsSI": 200000,
        "addOns": [],
        "paSelection": {
            "proposer": True,
            "spouse": True
        },
        "discountPercentage": 10,
        "loadingPercentage": 15
    }
    
    response = requests.post(f"{BASE_URL}/api/fire/ubgr/calculate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        breakdown = data['breakdown']
        
        print(f"✅ Status: {response.status_code}")
        print(f"\nKey Validations:")
        
        # Validate discount applies only to Basic Fire + Add-On
        discount_base = breakdown['basicFirePremium'] + breakdown['addOnPremium']
        expected_discount = discount_base * 0.10
        print(f"  Discount Base: {discount_base}")
        print(f"  Expected Discount (10%): {expected_discount:.2f}")
        print(f"  Actual Discount: {breakdown['discountAmount']}")
        assert abs(breakdown['discountAmount'] - expected_discount) < 0.01, "Discount calculation error"
        
        # Validate loading applies only to Subtotal
        expected_loading = breakdown['subtotal'] * 0.15
        print(f"  Subtotal: {breakdown['subtotal']}")
        print(f"  Expected Loading (15%): {expected_loading:.2f}")
        print(f"  Actual Loading: {breakdown['loadingAmount']}")
        assert abs(breakdown['loadingAmount'] - expected_loading) < 0.01, "Loading calculation error"
        
        # Validate terrorism is NOT included in discount/loading
        print(f"  Terrorism Premium: {breakdown['terrorismPremium']}")
        print(f"  Net Premium: {breakdown['netPremium']}")
        
        expected_net = breakdown['subtotal'] + breakdown['loadingAmount'] + breakdown['terrorismPremium']
        assert abs(breakdown['netPremium'] - expected_net) < 0.01, "Net Premium mismatch"
        
        print("\n✅ All validations passed")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_uvgs_no_terrorism():
    """Test UVGS does not include terrorism"""
    print("\n" + "="*60)
    print("TEST 3: UVGS (No Terrorism)")
    print("="*60)
    
    payload = {
        "productCode": "UVGS",
        "occupancyCode": "1001",
        "buildingSI": 1000000,
        "contentsSI": 200000,
        "addOns": [],
        "paSelection": {
            "proposer": False,
            "spouse": False
        },
        "discountPercentage": 0,
        "loadingPercentage": 0
    }
    
    response = requests.post(f"{BASE_URL}/api/fire/uvgs/calculate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        breakdown = data['breakdown']
        
        print(f"✅ Status: {response.status_code}")
        print(f"\nTerrorism Check:")
        print(f"  Terrorism Premium: {breakdown['terrorismPremium']}")
        
        # UVGS must NOT have terrorism
        if breakdown['terrorismPremium'] is None or breakdown['terrorismPremium'] == 0:
            print("✅ UVGS correctly excludes terrorism")
        else:
            print(f"❌ UVGS incorrectly includes terrorism: {breakdown['terrorismPremium']}")
        
        print(f"\n  Net Premium: {breakdown['netPremium']}")
        print(f"  Gross Premium: {breakdown['grossPremium']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_invalid_product():
    """Test invalid product code"""
    print("\n" + "="*60)
    print("TEST 4: Invalid Product Code")
    print("="*60)
    
    payload = {
        "productCode": "INVALID",
        "occupancyCode": "1001",
        "buildingSI": 1000000,
        "contentsSI": 0,
        "addOns": [],
        "paSelection": {"proposer": False, "spouse": False},
        "discountPercentage": 0,
        "loadingPercentage": 0
    }
    
    response = requests.post(f"{BASE_URL}/api/fire/ubgr/calculate", json=payload)
    
    if response.status_code == 400:
        print(f"✅ Correctly rejected invalid product: {response.status_code}")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"❌ Should have returned 400, got {response.status_code}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("UBGR/UVGR/UVGS PREMIUM CALCULATION TEST SUITE")
    print("="*60)
    
    try:
        test_ubgr_basic()
        test_ubgr_with_discount_loading()
        test_uvgs_no_terrorism()
        test_invalid_product()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
