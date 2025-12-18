
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.routers.fire.risk_rate import get_fire_risk_rate, get_risk_rate
from app.models.fire_models import FireIibRate

def test_get_fire_risk_rate_found():
    # Mock DB Session
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    # Mock Result
    mock_rate = FireIibRate(iib_code="2001", rate_per_mille=1.5)
    mock_filter.first.return_value = mock_rate
    
    # Call
    rate = get_fire_risk_rate("2001", mock_db)
    
    assert rate == 1.5
    # Verify query
    mock_db.query.assert_called_with(FireIibRate)

def test_get_fire_risk_rate_not_found():
    # Mock DB Session
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    # Mock Result None
    mock_filter.first.return_value = None
    
    # Call and Assert Exception
    with pytest.raises(HTTPException) as exc:
        get_fire_risk_rate("9999", mock_db)
    
    assert exc.value.status_code == 404
    assert "Risk rate not found" in exc.value.detail

def test_api_endpoint_structure():
    # Mock DB
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    mock_rate = FireIibRate(iib_code="2001", rate_per_mille=2.5)
    mock_filter.first.return_value = mock_rate
    
    # Call API function directly
    response = get_risk_rate(iib_code="2001", db=mock_db)
    
    assert response["iib_code"] == "2001"
    assert response["risk_rate_per_mille"] == 2.5
    assert "iib_code" in response
    assert "risk_rate_per_mille" in response

def test_api_strips_whitespace():
    # Mock DB
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    mock_rate = FireIibRate(iib_code="2001", rate_per_mille=2.5)
    mock_filter.first.return_value = mock_rate
    
    # Call API with whitespace
    response = get_risk_rate(iib_code=" 2001 ", db=mock_db)
    
    assert response["iib_code"] == "2001"
    assert response["risk_rate_per_mille"] == 2.5
