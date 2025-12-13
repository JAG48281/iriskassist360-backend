import sys
import os

# Ensure app is importable
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_checks():
    with open("verify_master_log.txt", "w", encoding="utf-8") as f:
        f.write("--- Starting Verification ---\n")
        
        # Check 1: BGRP
        f.write("\n[CHECK 1] BGRP (Residential)\n")
        try:
            response = client.get("/api/master/risk-descriptions?productCode=BGRP")
            if response.status_code != 200:
                f.write(f"FAILED: Status {response.status_code}, {response.text}\n")
            else:
                data = response.json()
                f.write(f"Success. Items returned: {len(data)}\n")
                if data:
                    f.write(f"Sample: {data[0]}\n")
                    # Validation
                    if data[0]['iibCode'] in ['1001', '1001_2']:
                        f.write("Validation Passed: iibCode is 1001 or 1001_2\n")
                    else:
                        f.write(f"FAILURE: iibCode unexpected: {data[0]['iibCode']}\n")
                else:
                    f.write("WARNING: No data returned from DB for BGRP.\n")
        except Exception as e:
            f.write(f"EXCEPTION: {e}\n")

        # Check 2: BSUS
        f.write("\n[CHECK 2] BSUS (Commercial)\n")
        try:
            response = client.get("/api/master/risk-descriptions?productCode=BSUS")
            if response.status_code != 200:
                f.write(f"FAILED: Status {response.status_code}, {response.text}\n")
            else:
                data = response.json()
                f.write(f"Success. Items returned: {len(data)}\n")
                if data:
                    # Validation
                    if data[0]['iibCode'] in ['1001', '1001_2']:
                        f.write("FAILED: Found Residential code in BSUS list!\n")
                    else:
                        f.write("Validation Passed: No Residential codes found in sample.\n")
        except Exception as e:
            f.write(f"EXCEPTION: {e}\n")

        # Check 3: Invalid
        f.write("\n[CHECK 3] Invalid Code\n")
        try:
            response = client.get("/api/master/risk-descriptions?productCode=XYZ")
            if response.status_code == 400:
                f.write("Success. Got 400 Bad Request as expected.\n")
            else:
                f.write(f"FAILED: Expected 400, got {response.status_code}\n")
        except Exception as e:
            f.write(f"EXCEPTION: {e}\n")

if __name__ == "__main__":
    run_checks()
    print("LOG WRITTEN")
