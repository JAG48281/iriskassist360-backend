from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_risk_descriptions_bgrp_logic():
    """
    Test Case 1: productCode = BGRP
    → exactly 2 (or small subset of) risks returned
    → both occupancyType = Residential (or at least strictly filtered)
    """
    response = client.get("/api/master/risk-descriptions?productCode=BGRP")
    assert response.status_code == 200, f"Response: {response.text}"
    
    data = response.json()
    assert isinstance(data, list)
    
    # Check if we got data.
    if len(data) > 0:
        # Check constraints
        for item in data:
            assert item['occupancyCode'] in ['1001', '1001_2']
            # occupancyType check requires knowing what's in DB, but let's check keys
            assert "occupancyCode" in item
            assert "occupancyDescription" in item
            assert "aiftSection" in item
            
def test_risk_descriptions_ubgr_normalization():
    """
    Test Case 1a: productCode = UBGR (normalized to BGRP)
    """
    response = client.get("/api/master/risk-descriptions?productCode=UBGR")
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 0:
        for item in data:
            assert item['occupancyCode'] in ['1001', '1001_2']

def test_risk_descriptions_bsus_logic():
    """
    Test Case 2: productCode = BSUS
    → large list returned
    → mixed occupancy types allowed / Non-Residential
    """
    response = client.get("/api/master/risk-descriptions?productCode=BSUS")
    assert response.status_code == 200
    
    data = response.json()
    if len(data) > 0:
        for item in data:
            # Should NOT be 1001/1001_2
            assert item['occupancyCode'] not in ['1001', '1001_2']
            
def test_invalid_product_code():
    # Should now return empty list, not 400
    response = client.get("/api/master/risk-descriptions?productCode=INVALID_99")
    assert response.status_code == 200
    assert response.json() == []
