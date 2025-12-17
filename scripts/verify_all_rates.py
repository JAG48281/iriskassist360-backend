
import sys
import os
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def check_ubgr():
    print("Checking UBGR...")
    resp = client.get("/api/master/risk-rate?iib_code=1001")
    if resp.status_code == 200 and resp.json()['risk_rate_per_mille'] == 0.15:
        print("✅ UBGR OK")
    else:
        print(f"❌ UBGR FAILED: {resp.status_code} {resp.text}")

def check_bsus():
    print("Checking BSUS...")
    resp = client.get("/api/master/bsus-risk-rate?iib_code=1006&eq_zone=Zone I")
    if resp.status_code == 200 and resp.json()['product'] == 'BSUS' and isinstance(resp.json()['risk_rate_per_mille'], float):
        print("✅ BSUS OK")
    else:
        print(f"❌ BSUS FAILED: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    check_ubgr()
    check_bsus()
