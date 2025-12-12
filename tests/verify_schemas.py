import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def test_field_schemas():
    results = {}
    
    # Test occupancies
    print("Testing /api/occupancies...")
    resp = requests.get(f"{BASE_URL}/api/occupancies", timeout=10)
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        if data:
            sample = data[0]
            results["occupancies"] = {
                "status": "OK",
                "fields": list(sample.keys()),
                "has_required": all(k in sample for k in ["iib_code", "section", "description"]),
                "sample": sample
            }
    
    # Test add-on-rates
    print("Testing /api/add-on-rates...")
    resp = requests.get(f"{BASE_URL}/api/add-on-rates", timeout=10)
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        if data:
            sample = data[0]
            results["add_on_rates"] = {
                "status": "OK",
                "fields": list(sample.keys()),
                "has_required": all(k in sample for k in ["add_on_code", "product_code", "rate_type", "rate_value", "occupancy_rule"]),
                "sample": sample
            }
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    test_field_schemas()
