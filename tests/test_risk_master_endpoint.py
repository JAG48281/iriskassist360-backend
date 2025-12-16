from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_risk_descriptions_bgrp_logic():
    response = client.get("/api/master/risk-descriptions?productCode=BGRP")
    assert response.status_code == 200, f"Response: {response.text}"
    
    json_resp = response.json()
    assert json_resp["success"] is True
    data = json_resp["data"]
    assert isinstance(data, list)
    
    if len(data) > 0:
        for item in data:
            assert item['iib_code'] in ['1001', '1001_2']
            assert "id" in item
            assert "description" in item
            assert "occupancy_type" in item
            assert "aift_section" in item

def test_risk_descriptions_ubgr_normalization():
    response = client.get("/api/master/risk-descriptions?productCode=UBGR")
    assert response.status_code == 200
    json_resp = response.json()
    data = json_resp["data"]
    
    if len(data) > 0:
        for item in data:
            assert item['iib_code'] in ['1001', '1001_2']

def test_risk_descriptions_bsus_logic():
    response = client.get("/api/master/risk-descriptions?productCode=BSUS")
    assert response.status_code == 200
    
    json_resp = response.json()
    data = json_resp["data"]
    
    if len(data) > 0:
        for item in data:
            assert item['iib_code'] not in ['1001', '1001_2']
            
def test_invalid_product_code():
    response = client.get("/api/master/risk-descriptions?productCode=INVALID_99")
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["data"] == []
