"""
Integration test script for Fire Risk Rate API
Demonstrates end-to-end functionality
"""
import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your deployed URL
API_ENDPOINT = f"{BASE_URL}/api/fire/risk-rate"


def test_endpoint(product_code, iib_code, aift_section, expected_status=200):
    """Test a single endpoint call"""
    params = {
        "productCode": product_code,
        "iibCode": iib_code,
        "aiftSection": aift_section
    }
    
    print(f"\n🧪 Testing: {product_code} | IIB: {iib_code} | Section: {aift_section}")
    
    try:
        response = requests.get(API_ENDPOINT, params=params)
        print(f"   Status: {response.status_code}")
        
        data = response.json()
        print(f"   Response: {data}")
        
        if response.status_code == expected_status:
            print(f"   ✅ PASS")
            return True
        else:
            print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Fire Risk Rate API - Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: UBGR normalization to BGRP
    print("\n📋 Test 1: UBGR → BGRP Normalization")
    results.append(test_endpoint("UBGR", "1001", "A", expected_status=200))
    
    # Test 2: BGRP with valid IIB code
    print("\n📋 Test 2: BGRP Valid IIB Code")
    results.append(test_endpoint("BGRP", "1001", "A", expected_status=200))
    
    # Test 3: SFSP product
    print("\n📋 Test 3: SFSP Product")
    results.append(test_endpoint("SFSP", "2001", "A", expected_status=200))
    
    # Test 4: IAR product
    print("\n📋 Test 4: IAR Product")
    results.append(test_endpoint("IAR", "3006", "A", expected_status=200))
    
    # Test 5: BSUS product with zone
    print("\n📋 Test 5: BSUS with Zone")
    results.append(test_endpoint("BSUS", "1002", "Zone I", expected_status=200))
    
    # Test 6: BLUS product with zone
    print("\n📋 Test 6: BLUS with Zone")
    results.append(test_endpoint("BLUS", "1003", "Zone II", expected_status=200))
    
    # Test 7: UVUS product with zone
    print("\n📋 Test 7: UVUS with Zone")
    results.append(test_endpoint("UVUS", "1004", "Zone III", expected_status=200))
    
    # Test 8: UVGR product
    print("\n📋 Test 8: UVGR Product")
    results.append(test_endpoint("UVGR", "1005", "Zone I", expected_status=200))
    
    # Test 9: Invalid IIB code (should return 404)
    print("\n📋 Test 9: Invalid IIB Code (404)")
    results.append(test_endpoint("BGRP", "INVALID_CODE", "A", expected_status=404))
    
    # Test 10: Invalid product code (should return 400)
    print("\n📋 Test 10: Invalid Product Code (400)")
    results.append(test_endpoint("INVALID", "1001", "A", expected_status=400))
    
    # Test 11: Case insensitivity
    print("\n📋 Test 11: Case Insensitive Product Code")
    results.append(test_endpoint("bgrp", "1001", "A", expected_status=200))
    
    # Test 12: Whitespace handling
    print("\n📋 Test 12: Whitespace in Product Code")
    results.append(test_endpoint("  BGRP  ", "1001", "A", expected_status=200))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
