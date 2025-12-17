"""
Integration test for UBGR Risk Rate Auto-fill Fix
Tests the /calculate endpoint with realistic payloads
"""
import requests
import json


def test_calculate_endpoint():
    """Test the /calculate endpoint with UBGR product"""
    
    base_url = "http://localhost:8000"
    endpoint = "/calculate"
    
    # Test Case 1: UBGR with occupancyId 597 (IIB code 1001)
    payload_1 = {
        "occupancyId": 597,
        "productCode": "UBGR"
    }
    
    print("=" * 70)
    print("UBGR RISK RATE AUTO-FILL - INTEGRATION TEST")
    print("=" * 70)
    
    print(f"\n📤 Request Payload:")
    print(json.dumps(payload_1, indent=2))
    
    try:
        response = requests.post(f"{base_url}{endpoint}", json=payload_1, timeout=10)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            risk_rate = data.get("meta", {}).get("risk_rate")
            
            if risk_rate:
                print(f"\n✅ SUCCESS: Risk Rate = {risk_rate}‰")
                print("✅ UBGR Risk Rate Auto-fill is WORKING!")
            else:
                print("\n❌ FAIL: Risk rate is missing from response")
        else:
            print(f"\n❌ FAIL: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n⚠️  Server not running. Please start the server with:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_calculate_endpoint()
