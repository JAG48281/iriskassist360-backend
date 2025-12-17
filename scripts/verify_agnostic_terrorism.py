
import sys
import os
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def verify_agnostic_terrorism():
    print("Verifying Product-Independent Terrorism Logic...")
    
    # 1. Test Endpoint (No Product Code)
    print("\n1. Testing GET /api/fire/terrorism-rate...")
    resp = client.get("/api/fire/terrorism-rate?occupancy_type=Residential&total_sum_insured=1000000")
    if resp.status_code == 200:
        d = resp.json()
        print(f"✅ Endpoint Success: Rate={d['terrorism_rate_per_mille']}")
        # User requirement check: Residential 10L -> 0.10
        if d['terrorism_rate_per_mille'] == 0.10:
             print("✅ Rate confirmed as 0.10 (Validation Case)")
        else:
             print(f"⚠️ Rate is {d['terrorism_rate_per_mille']}. Check slab data.")
    else:
        print(f"❌ Endpoint Failed: {resp.status_code} {resp.text}")

    # 2. Test Premium Calculation (UBGR)
    # Should use the same rate resolver logic.
    print("\n2. Testing Premium Calculation (UBGR)...")
    payload = {
        "productCode": "UBGR",
        "iib_code": "1001",
        "total_si": 1000000.0,
        "risk_rate": 0.15
    }
    resp = client.post("/api/calculate", json=payload)
    if resp.status_code == 200:
        d = resp.json()
        used_rate = d.get('terrorism_rate_used')
        print(f"✅ Calculation Success. Terrorism Rate Used: {used_rate}")
        
        # Determine exact expected premium
        exp_rate = 0.10 # Based on step 1
        exp_prem = 1000000 * exp_rate / 1000 # = 100
        
        if used_rate is not None and abs(used_rate - exp_rate) < 0.001:
             print(f"✅ Calculation verified using agnostic rate {used_rate}")
        elif used_rate == 0.07:
             print("⚠️ Used Fallback 0.07? (Maybe logic caught exception?)")
        else:
             print(f"❓ Unexpected rate used: {used_rate}")

    else:
        print(f"❌ Calc Failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    verify_agnostic_terrorism()
