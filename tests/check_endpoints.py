import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

ENDPOINTS = [
    "/api/occupancies",
    "/api/product-basic-rates",
    "/api/stfi-rates",
    "/api/eq-rates",
    "/api/terrorism-slabs",
    "/api/add-on-master",
    "/api/add-on-product-map",
    "/api/add-on-rates"
]

def check_endpoint(endpoint):
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            return {
                "status": resp.status_code,
                "ok": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}"
            }
        
        data = resp.json()
        
        # Handle ResponseModel wrapper
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        else:
            items = data
            
        if not isinstance(items, list):
            return {
                "status": 200,
                "ok": False,
                "error": "Response is not a list"
            }
        
        count = len(items)
        sample = items[:3] if count > 0 else []
        
        return {
            "status": 200,
            "count": count,
            "sample": sample,
            "ok": True
        }
        
    except Exception as e:
        return {
            "status": -1,
            "ok": False,
            "error": str(e)
        }

def main():
    results = {}
    
    for endpoint in ENDPOINTS:
        print(f"Checking {endpoint}...", file=sys.stderr)
        result = check_endpoint(endpoint)
        results[endpoint] = result
        
        if not result["ok"]:
            print(f"FAILED: {endpoint}", file=sys.stderr)
            print(f"Error: {result.get('error')}", file=sys.stderr)
            print(json.dumps({"endpoint_results": results}, indent=2))
            sys.exit(1)
        
        if result.get("count", 0) == 0:
            print(f"WARNING: {endpoint} returned empty list", file=sys.stderr)
    
    print(json.dumps({"endpoint_results": results}, indent=2))

if __name__ == "__main__":
    main()
