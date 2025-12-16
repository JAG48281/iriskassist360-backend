
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/calculate"

def run_tests():
    print("=== API VERIFICATION SUITE ===\n")
    failed = False
    
    # CASE 1: UBGR 1001 -> 0.15
    print("1. UBGR 1001 (Expect 0.15)")
    try:
        r = requests.post(BASE_URL, json={"product_code": "UBGR", "occupancy_id": 1001, "eq_zone": "Zone IV"}) 
        # Zone IV passed to see if it ignores it. UBGR should ignore.
        if r.status_code == 200:
            res = r.json()
            rate = res['data']['meta']['risk_rate']
            if float(rate) == 0.15:
                print(f"   [PASS] Rate: {rate}")
            else:
                print(f"   [FAIL] Expected 0.15, Got {rate}")
                failed = True
        else:
             print(f"   [FAIL] API Error {r.status_code}")
             failed = True
    except Exception as e:
        print(f"   [FAIL] Exception {e}")
        failed = True

    # CASE 2: SFSP 1001 -> 0.15 (And FREE checks?)
    print("\n2. SFSP 1001 (Expect 0.15)")
    try:
        # Note: SFSP usually requires EQ logic so pass zone
        r = requests.post(BASE_URL, json={"product_code": "SFSP", "occupancy_id": 1001, "eq_zone": "Zone III"})
        if r.status_code == 200:
            res = r.json()
            rate = res['data']['meta']['risk_rate']
            if float(rate) == 0.15:
                print(f"   [PASS] Rate: {rate}")
            else:
                print(f"   [FAIL] Expected 0.15, Got {rate}")
                failed = True
        else:
             print(f"   [FAIL] API Error {r.status_code} {r.text}")
             failed = True
    except Exception as e:
        print(f"   [FAIL] Exception {e}")
        failed = True
        
    # CASE 3: BSUS 1002 Zone I -> 0.455
    print("\n3. BSUS 1002 Zone I (Expect 0.455)")
    try:
        r = requests.post(BASE_URL, json={"product_code": "BSUS", "occupancy_id": 1002, "eq_zone": "Zone I"})
        if r.status_code == 200:
            res = r.json()
            rate = res['data']['meta']['risk_rate']
            if float(rate) == 0.455:
                print(f"   [PASS] Rate: {rate}")
            else:
                print(f"   [FAIL] Expected 0.455, Got {rate}")
                failed = True
        else:
             print(f"   [FAIL] API Error {r.status_code} {r.text}")
             failed = True
    except Exception as e:
        print(f"   [FAIL] Exception {e}")
        failed = True

    # CASE 4: ADD-ON LOGIC CHECK
    # We can check specific add-ons if we had an endpoint that returns breakdown for simple inputs.
    # Currently /calculate returns basic rate meta. 
    # To check Add-On Pricing, we need to call the premium calc endpoint: /api/fire/ubgr/calculate (or similar)
    # But those require valid payloads.
    # For now, we verified the basic Rates 1,2,3 which was the core request.
    
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
