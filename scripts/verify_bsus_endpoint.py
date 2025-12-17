
import sys
import os
import requests

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def test_bsus_rate(iib_code, eq_zone):
    logger.info(f"Testing iib_code={iib_code}, eq_zone={eq_zone}...")
    response = client.get(f"/api/master/bsus-risk-rate?iib_code={iib_code}&eq_zone={eq_zone}")
    
    if response.status_code != 200:
        logger.error(f"Failed: Status {response.status_code}, Response: {response.text}")
        return False
        
    data = response.json()
    logger.info(f"Response: {data}")
    
    # Check structure
    if "risk_rate_per_mille" not in data or "iib_code" not in data or "eq_zone" not in data or "product" not in data:
        logger.error("Failed: Missing keys in response")
        return False
        
    # Check types
    if not isinstance(data["risk_rate_per_mille"], (int, float)):
        logger.error(f"Failed: risk_rate_per_mille is not a number: {type(data['risk_rate_per_mille'])}")
        return False

    if data["product"] != "BSUS":
         logger.error("Failed: Product is not BSUS")
         return False

    logger.info("✅ Success")
    return True

def main():
    success = True
    
    # Test valid case
    if not test_bsus_rate("1006", "Zone I"):
        success = False
        
    # Test Not Found
    logger.info("Testing invalid zone...")
    response = client.get("/api/master/bsus-risk-rate?iib_code=1006&eq_zone=Zone X")
    if response.status_code != 404:
        logger.error(f"Failed: Expected 404, got {response.status_code}")
        success = False
    else:
        logger.info("✅ Success (404 received)")

    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
