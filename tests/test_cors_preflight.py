"""
CORS Preflight Test Script
Tests OPTIONS requests to ensure CORS is properly configured
This simulates browser behavior
"""
import requests
import sys

BASE_URL = "http://localhost:8000"  # Change to Railway URL for production testing
RISK_DESCRIPTIONS_ENDPOINT = f"{BASE_URL}/api/master/risk-descriptions"

def test_options_preflight():
    """Test OPTIONS preflight request (what the browser sends)"""
    print("=" * 60)
    print("Testing CORS Preflight (OPTIONS request)")
    print("=" * 60)
    
    headers = {
        "Origin": "http://localhost:50000",  # Simulating Flutter Web origin
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    
    print(f"\n📤 Sending OPTIONS request to: {RISK_DESCRIPTIONS_ENDPOINT}")
    print(f"   Headers: {headers}")
    
    try:
        response = requests.options(RISK_DESCRIPTIONS_ENDPOINT, headers=headers)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"   Response Headers:")
        for header, value in response.headers.items():
            if "access-control" in header.lower():
                print(f"      {header}: {value}")
        
        if response.status_code == 200:
            print("\n✅ PASS: OPTIONS request returned 200")
            
            # Check required CORS headers
            required_headers = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers"
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in [h.lower() for h in response.headers.keys()]:
                    missing_headers.append(header)
            
            if missing_headers:
                print(f"⚠️  WARNING: Missing CORS headers: {missing_headers}")
                return False
            else:
                print("✅ All required CORS headers present")
                return True
        
        elif response.status_code == 502:
            print("❌ FAIL: Got 502 (Bad Gateway) - Backend not handling OPTIONS properly")
            print("   This is the exact error browsers report as 'CORS error'")
            return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_actual_get_request():
    """Test actual GET request (what the browser sends after successful preflight)"""
    print("\n" + "=" * 60)
    print("Testing Actual GET Request (after preflight)")
    print("=" * 60)
    
    params = {"productCode": "BGRP"}
    headers = {"Origin": "http://localhost:50000"}
    
    print(f"\n📤 Sending GET request to: {RISK_DESCRIPTIONS_ENDPOINT}")
    print(f"   Params: {params}")
    print(f"   Headers: {headers}")
    
    try:
        response = requests.get(RISK_DESCRIPTIONS_ENDPOINT, params=params, headers=headers)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('success', False)}")
            print(f"   Data items: {len(data.get('data', []))}")
            
            # Check CORS headers on actual response
            if "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]:
                print("✅ CORS headers present on GET response")
            else:
                print("⚠️  WARNING: CORS headers missing on GET response")
            
            # Validate response format
            if "success" in data and "data" in data:
                print("✅ Response format is correct")
                
                if data["data"]:
                    sample = data["data"][0]
                    required_keys = ["id", "description", "occupancy_type", "aift_section", "iib_code"]
                    if all(key in sample for key in required_keys):
                        print("✅ Data structure is correct")
                        return True
                    else:
                        print(f"❌ FAIL: Missing required keys in data. Sample: {sample}")
                        return False
                else:
                    print("⚠️  WARNING: No data returned (might be OK if no occupancies)")
                    return True
            else:
                print(f"❌ FAIL: Invalid response format: {data}")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_cors_from_different_origins():
    """Test CORS from different origins"""
    print("\n" + "=" * 60)
    print("Testing CORS from Different Origins")
    print("=" * 60)
    
    origins = [
        "http://localhost:50000",
        "http://localhost:3000",
        "https://example.com",
        "https://iriskassist360.com"
    ]
    
    all_passed = True
    
    for origin in origins:
        print(f"\n🧪 Testing origin: {origin}")
        headers = {"Origin": origin}
        
        try:
            response = requests.options(RISK_DESCRIPTIONS_ENDPOINT, headers=headers)
            
            if response.status_code == 200:
                allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
                if allow_origin == "*" or allow_origin == origin:
                    print(f"   ✅ PASS: {origin}")
                else:
                    print(f"   ❌ FAIL: Access-Control-Allow-Origin = {allow_origin}")
                    all_passed = False
            else:
                print(f"   ❌ FAIL: Status {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all CORS tests"""
    print("\n🔍 CORS Preflight Test Suite")
    print("Testing backend CORS configuration for browser compatibility\n")
    
    results = []
    
    # Test 1: OPTIONS preflight
    results.append(("OPTIONS Preflight", test_options_preflight()))
    
    # Test 2: Actual GET request
    results.append(("GET Request", test_actual_get_request()))
    
    # Test 3: Multiple origins
    results.append(("Multiple Origins", test_cors_from_different_origins()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All CORS tests passed! Browser should work correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Review backend CORS configuration.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
