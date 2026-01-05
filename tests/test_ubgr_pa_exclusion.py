
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.fire_premium_service import FirePremiumCalculator
from app.schemas.fire_premium import UBGRUVGRRequest, AddOnItem, PASelection

@pytest.fixture
def mock_rating_engine():
    with patch("app.services.fire_premium_service.get_basic_rate_per_mille") as mock_basic, \
         patch("app.services.fire_premium_service.get_add_on_rate") as mock_addon, \
         patch("app.services.fire_premium_service.calculate_terrorism_premium") as mock_terr_prem, \
         patch("app.services.fire_premium_service.get_occupancy_details") as mock_occ:
         
        # Setup Defaults
        mock_basic.return_value = Decimal("0.50") # 0.5 per mille
        
        # Mock Add-on Rate (for PA)
        # Returns (rate_type, value)
        def side_effect_addon(product_code, add_on_code, occupancy_code):
            if add_on_code == "PA_PROPOSER":
                return "fixed", Decimal("100.0") # Fixed 100 Rs
            if add_on_code == "PA_SPOUSE":
                return "fixed", Decimal("50.0") # Fixed 50 Rs
            return "per_mille", Decimal("0.50")
            
        mock_addon.side_effect = side_effect_addon
        
        mock_terr_prem.return_value = Decimal("200.0")
        mock_occ.return_value = {"occupancy_type": "Residential"}
        
        yield {
            "basic": mock_basic,
            "addon": mock_addon,
            "terr": mock_terr_prem
        }

def test_ubgr_pa_exclusion_from_total_si(mock_rating_engine):
    """
    Validate that PA SIs are EXCLUDED from Total Property SI and Terrorism SI base.
    """
    payload = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000,
        contentsSI=500000,
        lossOfRentSI=10000,
        altAccommodationSI=20000,
        valuableContentsSI=5000,
        
        # PA SIs - Should be EXCLUDED
        paProposerSI=500000,
        paSpouseSI=500000,
        paSelection=PASelection(proposer=True, spouse=True),
        
        terrorism_si=0, # Should default to Total Property SI
        addOns=[AddOnItem(addOnCode="TERRORISM", sumInsured=0)],
        
        risk_rate_per_mille=0.5
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(payload)
    
    print("\nResult Breakdown:", result)
    
    # 1. Verify Total Property SI
    # Should be: Building(10L) + Contents(5L) + Rent(10k) + AltAcc(20k) + Val(5k)
    # = 1,535,000
    expected_si = 1000000 + 500000 + 10000 + 20000 + 5000
    assert result["total_property_si"] == expected_si
    
    # 2. Verify basic_fire_premium using ONLY Building SI (New Logic)
    # Building SI = 1,000,000. Rate = 0.5 per mille.
    # Premium = 1,000,000 * 0.5 / 1000 = 500
    assert result["basic_fire_premium"] == 500.0
    
    # 3. Verify PA Premium is Separate
    # Mock returned 100 for Proposer, 50 for Spouse
    assert result["pa_proposer_premium"] == 100.0
    assert result["pa_spouse_premium"] == 50.0
    
    # 3b. Verify Add-on Premium (Contents + Property Add-ons)
    # Add-on SI = Contents(500k) + Rent(10k) + AltAcc(20k) + Val(5k) = 535,000
    # Rate = 0.5
    # Premium = 535,000 * 0.5 / 1000 = 267.5 -> 268 (Round)
    assert result["add_on_premium"] == 268.0
    
    # 4. Verify Terrorism SI matches Base Core SI (Building + Contents) 
    # Logic Update: Terrorism SI = Building + Contents (Strict) = 1,500,000 (Excl LOR/AltAcc)
    expected_terr_si = 1000000 + 500000
    assert result["terrorism_si"] == expected_terr_si
    
    # 5. Verify New Fields
    assert result["fire_sum_insured"] == expected_si
    assert result["total_sum_insured"] == expected_si

