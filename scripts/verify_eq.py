import requests
import sys

BASE_URL = "http://localhost:8000/api/calculate"
# We need to test the fire premium calc, which is likely under /api/fire/ubgr/calculate or similar 
# BUT the user asked to verify the EQ logic. 
# The recent changes were in `FirePremiumCalculator`. 
# The endpoints using it are likely /api/fire/ubgr/calculate (mapped in fire/fire_premium.py?)
# Let's check `app/routers/fire/fire_premium.py` route naming.
# Or try the unified calculate? No, Unified uses `get_basic_rate`. 
# The STRICT EQ logic is in `FirePremiumCalculator.calculate_ubgr_uvgr`.
# I need to find which endpoint exposes this. 
# Usually `app/routers/fire/fire_premium.py`.

def test_eq_logic():
    # 1. Test UBGR (Should IGNORE EQ)
    # 2. Test SFSP/Other (Should REQUIRE EQ if I can access it via same endpoint? 
    # Warning: `calculate_ubgr_uvgr` suggests it's for UBGR/UVGR. 
    # If I pass `productCode: SFSP` to it, will it work? 
    # Code allows `if product_code not in ['UBGR', 'UVGR', 'UVGS']`. 
    # Wait, line 130 checks: `if product_code not in ['UBGR', 'UVGR', 'UVGS']: raise`
    # So I can ONLY test UBGR, UVGR, UVGS.
    # UVGR/UVGS might require EQ? 
    # User prompt: "EQ is applicable only to SFSP, UVUS, BLUS, IAR, UVGR".
    # So UVGR should trigger EQ logic!
    
    url = "http://localhost:8000/api/fire/ubgr/calculate" 
    # Assumption on URL. Let's verify route first.
    
    print("Testing EQ Logic via Fire Premium Endpoint...")
    
    # CASE 1: UBGR (Should be 0 EQ)
    payload_ubgr = {
        "productCode": "UBGR",
        "occupancyCode": "1001",
        "buildingSI": 1000000,
        "contentsSI": 0,
        "policyPeriod": 1,
        "eqZone": "Zone IV" # Should be ignored
    }
    
    try:
        r = requests.post(url, json=payload_ubgr)
        if r.status_code == 200:
            res = r.json()
            net = res['data']['breakdown']['net_premium']
            # EQ premium is not explicit in breakdown model? 
            # I added eq_premium to Net, but didn't add strict field to schema?
            # I updated `PremiumBreakdown` instantiation?? 
            # I passed `net_premium=final_net`. 
            # I didn't add `eq_premium` to the breakdown OBJECT in the code Step 400.
            # I calculated it and added to NET.
            # So I can verify by checking if Net includes it.
            # Base UBGR Rate for 1001 is 0.15. Premium = 150.
            # Net should be ~150 + Terr + GST?
            print(f"UBGR Response: {r.status_code} Net={net}")
        else:
            print(f"UBGR Calc Failed: {r.text}")
    except Exception as e:
        print(f"Test Error: {e}")

    # CASE 2: UVGR (Should REQUIRE EQ logic)
    # Rate for 2001 Zone IV?
    payload_uvgr = {
        "productCode": "UVGR",
        "occupancyCode": "2001", # Industrial
        "buildingSI": 1000000,
        "eqZone": "Zone IV"
    }
    # If 2001 rate is say 0.37 (fire) + EQ?
    
    try:
        r2 = requests.post(url, json=payload_uvgr)
        # Note: If EQ logic is active for UVGR, and I provide Zone IV...
        # It should calculate.
        # IF I remove Zone, it should fail.
        print(f"UVGR Response: {r2.status_code}")
        if r2.status_code == 200:
             print(r2.json()['data']['breakdown'])
    except:
        pass

if __name__ == "__main__":
    test_eq_logic()
