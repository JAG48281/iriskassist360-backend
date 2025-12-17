"""
Tests for Fire Risk Rate API Endpoint
Tests all requirements specified in the objective:
- Product normalization (UBGR → BGRP)
- Valid IIB code returns correct rate
- Invalid combination returns 404
- Response keys exactly match expectations
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestFireRiskRateAPI:
    """Test suite for /api/fire/risk-rate endpoint"""
    
    def test_ubgr_normalization_to_bgrp(self):
        """Test that UBGR is correctly normalized to BGRP"""
        # UBGR should be normalized to BGRP and return a rate
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "UBGR",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
        assert isinstance(data["rate_per_mille"], (int, float))
        assert data["rate_per_mille"] > 0
    
    def test_bgrp_valid_iib_code_returns_correct_rate(self):
        """Test that BGRP with valid IIB code returns correct rate"""
        # Based on fire_iib_rates.csv: iib_code 1001 should return 0.15
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
        assert data["rate_per_mille"] == 0.15  # From CSV
    
    def test_sfsp_valid_iib_code_returns_rate(self):
        """Test that SFSP product with valid IIB code returns rate"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "SFSP",
                "iibCode": "2001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
        assert data["rate_per_mille"] == 0.37  # From CSV
    
    def test_bsus_valid_iib_code_returns_rate(self):
        """Test that BSUS product with valid IIB code returns rate"""
        # BSUS should query fire_bsus_rates table
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BSUS",
                "iibCode": "1002",
                "aiftSection": "Zone I"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
        assert isinstance(data["rate_per_mille"], (int, float))
        assert data["rate_per_mille"] > 0
    
    def test_blus_valid_iib_code_returns_rate(self):
        """Test that BLUS product with valid IIB code returns rate"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BLUS",
                "iibCode": "1003",
                "aiftSection": "Zone II"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
        assert isinstance(data["rate_per_mille"], (int, float))
    
    def test_uvus_valid_iib_code_returns_rate(self):
        """Test that UVUS product with valid IIB code returns rate"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "UVUS",
                "iibCode": "1004",
                "aiftSection": "Zone III"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
    
    def test_uvgr_valid_iib_code_returns_rate(self):
        """Test that UVGR product with valid IIB code returns rate"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "UVGR",
                "iibCode": "1005",
                "aiftSection": "Zone I"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rate_per_mille" in data
    
    def test_invalid_iib_code_returns_404(self):
        """Test that invalid IIB code combination returns 404"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "INVALID_CODE_99999",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["success"] is False
        assert "message" in data["detail"]
        assert "No rate found" in data["detail"]["message"]
    
    def test_response_keys_match_contract(self):
        """Test that response keys exactly match frontend expectations"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact keys
        assert set(data.keys()) == {"success", "rate_per_mille"}
        assert data["success"] is True
        assert isinstance(data["rate_per_mille"], (int, float))
    
    def test_invalid_product_code_returns_400(self):
        """Test that invalid product code returns 400"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "INVALID_PRODUCT",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["success"] is False
        assert "Invalid product code" in data["detail"]["message"]
    
    def test_missing_required_parameters(self):
        """Test that missing required parameters returns 422"""
        # Missing iibCode
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "aiftSection": "A"
            }
        )
        assert response.status_code == 422
        
        # Missing productCode
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        assert response.status_code == 422
        
        # Missing aiftSection
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "1001"
            }
        )
        assert response.status_code == 422
    
    def test_case_insensitive_product_code(self):
        """Test that product code is case insensitive"""
        # Lowercase
        response1 = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "bgrp",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        # Uppercase
        response2 = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        # Mixed case
        response3 = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BgRp",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # All should return the same rate
        rate1 = response1.json()["rate_per_mille"]
        rate2 = response2.json()["rate_per_mille"]
        rate3 = response3.json()["rate_per_mille"]
        
        assert rate1 == rate2 == rate3
    
    def test_multiple_iib_codes_bgrp_product(self):
        """Test multiple IIB codes for BGRP product"""
        test_cases = [
            ("1001", 0.15),
            ("1002", 0.22),
            ("2001", 0.37),
            ("3006", 0.52),
        ]
        
        for iib_code, expected_rate in test_cases:
            response = client.get(
                "/api/fire/risk-rate",
                params={
                    "productCode": "BGRP",
                    "iibCode": iib_code,
                    "aiftSection": "A"
                }
            )
            
            assert response.status_code == 200, f"Failed for IIB code {iib_code}"
            data = response.json()
            assert data["success"] is True
            assert data["rate_per_mille"] == expected_rate, \
                f"Expected {expected_rate} for IIB {iib_code}, got {data['rate_per_mille']}"
    
    def test_error_response_format(self):
        """Test that error responses follow the specified format"""
        # Test 404 error format
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "NONEXISTENT",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], dict)
        assert data["detail"]["success"] is False
        assert "message" in data["detail"]
        assert isinstance(data["detail"]["message"], str)
    
    def test_whitespace_handling_in_product_code(self):
        """Test that whitespace in product code is handled correctly"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "  BGRP  ",  # Leading and trailing spaces
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rate_per_mille"] == 0.15


class TestFireRiskRateBusinessLogic:
    """Test business logic and edge cases"""
    
    def test_iar_product_uses_iib_rates_table(self):
        """Test that IAR product queries fire_iib_rates table"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "IAR",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rate_per_mille"] == 0.15
    
    def test_rate_precision(self):
        """Test that rate values maintain proper precision"""
        response = client.get(
            "/api/fire/risk-rate",
            params={
                "productCode": "BGRP",
                "iibCode": "1001",
                "aiftSection": "A"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        rate = data["rate_per_mille"]
        
        # Rate should be a number with proper precision
        assert isinstance(rate, (int, float))
        # Rate should be positive
        assert rate > 0
        # Rate should be reasonable (less than 100 per mille seems reasonable for fire)
        assert rate < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
