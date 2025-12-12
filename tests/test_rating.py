from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_calculate_premium_basic():
    payload = {
        "product_name": "Test Product",
        "sum_insured": 100000,
        "rate": 1.5, # 1.5 per mille
        "discounts_pct": [],
        "loadings_pct": []
    }
    response = client.post("/api/rating/calculate", json=payload)
    if response.status_code != 200:
        print(response.json())
        
    assert response.status_code == 200
    data = response.json()
    # 100000 * 1.5/1000 = 150 base
    assert data["base_premium"] == 150.0
    assert data["total_premium"] > 150.0 # GST added

def test_calculate_premium_with_adjustments():
    payload = {
        "product_name": "Test Product",
        "sum_insured": 100000,
        "rate": 2.0, # 200 base
        "discounts_pct": [10.0], # 20 discount -> 180 net
        "loadings_pct": []
    }
    response = client.post("/api/rating/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["base_premium"] == 200.0
    assert data["net_premium"] == 180.0
