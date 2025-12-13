import sys
import os
sys.path.append(os.getcwd())
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def verify():
    print("Verifying Endpoint...")
    try:
        response = client.get("/api/master/risk-descriptions?productCode=BGRP")
        if response.status_code == 200:
            data = response.json()
            # Check keys correspond to schema, checking content
            print(f"Success. Data[0]: {data[0]}")
            # Ensure no internal server error about missing column
        else:
            print(f"Failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify()
