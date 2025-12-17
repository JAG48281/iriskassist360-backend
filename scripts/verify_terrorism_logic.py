
import sys
import os
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def verify_terrorism_logic():
    print("Verifying Terrorism Logic & Schema Changes...")
    
    # 1. Valid Request
    # Expectation: 
    # Occupancy 1001 = "Residential"
    # SI = 1M
    # Rate should be 0.1? Or user said 0.07 is default if failed?
    # User said: "Occupancy: Residential, Total SI: 10,00,000 -> Expected Rate: 0.10" in validation test case.
    # UBGR -> rate is 0.07? Prompt said "For UBGR -> rate is 0.07 per mille" (earlier prompt).
    # But later prompt "Occupancy Residential 10L -> 0.10".
    # And "Do NOT filter by product_code".
    # So if there is a slab for Residential 10L in DB, it should use it.
    
    # We will see what rate is returned in log or response 'terrorism_rate_used'.
    
    payload = {
        "productCode": "UBGR",
        "iib_code": "1001",
        "total_si": 1000000.0,
        "risk_rate": 0.15
    }
    
    print("\nTest 1: Valid Calc...")
    resp = client.post("/api/calculate", json=payload)
    if resp.status_code == 200:
        d = resp.json()
        print(f"✅ Success: {d}")
        
        # Check terrorism logic
        # Net = Fire + Terr
        # Fire = 150
        # If Rate = 0.07 -> Terr = 70 -> Net = 220
        # If Rate = 0.10 -> Terr = 100 -> Net = 250
        
        rate_used = d.get("terrorism_rate_used")
        print(f"Terrorism Rate Used: {rate_used}")
        
    else:
        print(f"❌ FAILED: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    verify_terrorism_logic()
