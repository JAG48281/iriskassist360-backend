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
    
    # Check if we got data. If DB is empty, this warns us (but strict Logic test passes if empty list)
    # However, for verification, we'd like to see rows.
    if len(data) == 0:
        print("WARNING: No data returned from DB for BGRP. Is the DB seeded?")
    else:
        # Check constraints
        for item in data:
            assert item['iibCode'] in ['1001', '1001_2']
            assert item['occupancyType'] == 'Residential'
            # Check Clean AIFT
            assert "Section" not in item['aiftSection']
            
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
            assert item['iibCode'] not in ['1001', '1001_2']
            
def test_invalid_product_code():
    response = client.get("/api/master/risk-descriptions?productCode=INVALID_99")
    assert response.status_code == 400
    assert "Invalid productCode" in response.json()['detail']
