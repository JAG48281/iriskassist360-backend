
import pytest
from decimal import Decimal
from app.services.fire_premium_service import FirePremiumCalculator
from app.schemas.fire_premium import UBGRUVGRRequest, PASelection, AddOnItem
from unittest.mock import patch

@pytest.fixture
def mock_rates():
    with patch('app.services.fire_premium_service.get_basic_rate_per_mille') as mock_basic, \
         patch('app.services.fire_premium_service.get_terrorism_rate_per_mille') as mock_terr, \
         patch('app.services.fire_premium_service.calculate_terrorism_premium') as mock_terr_calc, \
         patch('app.services.fire_premium_service.get_occupancy_details') as mock_occ, \
         patch('app.services.fire_premium_service.get_add_on_rate') as mock_addon:
        
        mock_basic.return_value = Decimal("0.15") # 0.15 per mille
        mock_terr.return_value = Decimal("0.07")  # For metadata
        # Mock terrorism premium calculation - returns 130
        mock_terr_calc.return_value = 130.0
        yield mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon

def test_ubgr_calculation_standard(mock_rates):
    mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True, "occupancy_type": "Non-Industrial"}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        contentsSI=500000.0, # Total 1.5M
        terrorism_si=1500000.0,
        addOns=[AddOnItem(addOnCode="TERRORISM", sumInsured=1500000.0)],
        discountPercentage=0,
        loadingPercentage=0,
        risk_rate_per_mille=0.15
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # 1.5M * 0.15 / 1000 = 225
    assert breakdown.basic_fire_premium == 150.0
    assert breakdown.add_on_premium == 75.0
    assert breakdown.subtotal == 225.0
    
    # Terrorism: 130 (mocked)
    assert breakdown.terrorism_premium == 130.0
    
    # Net: 225 + 130 = 355
    assert breakdown.net_premium == 355.0

def test_uvgr_calculation_no_terrorism(mock_rates):
    mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True}
    
    request = UBGRUVGRRequest(
        productCode="UVGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        contentsSI=0,
        terrorism_si=0,
        addOns=[],
        discountPercentage=0,
        loadingPercentage=0
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # 1M * 0.15 / 1000 = 150
    assert breakdown.basic_fire_premium == 150.0
    assert breakdown.terrorism_premium == 0.0
    assert breakdown.net_premium == 150.0

def test_loading_logic(mock_rates):
    mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True, "occupancy_type": "Non-Industrial"}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorism_si=1000000.0,
        addOns=[AddOnItem(addOnCode="TERRORISM", sumInsured=1000000.0)],
        discountPercentage=0,
        loadingPercentage=10, # 10% loading
        risk_rate_per_mille=0.15 
    )
    
    # Basic: 150, Subtotal: 150
    # Loading: 15, Terrorism: 130
    # Net: 150 + 15 + 130 = 295
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    assert breakdown.subtotal == 150.0
    assert breakdown.loading_amount == 15.0
    assert breakdown.terrorism_premium == 130.0
    assert breakdown.net_premium == 295.0

def test_discount_logic(mock_rates):
    mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True, "occupancy_type": "Non-Industrial"}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorism_si=1000000.0,
        addOns=[AddOnItem(addOnCode="TERRORISM", sumInsured=1000000.0)],
        discountPercentage=10, 
        loadingPercentage=0,
        risk_rate_per_mille=0.15
    )
    
    # Basic: 150, Subtotal: 150
    # Discount: 15, Terrorism: 130
    # Net: 150 - 15 + 130 = 265
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    assert breakdown.subtotal == 150.0
    assert breakdown.discount_amount == 15.0
    assert breakdown.net_premium == 265.0

def test_terrorism_si_isolation(mock_rates):
    """Verify terrorism is calculated on terrorism_si, not BuildingSI"""
    mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True, "occupancy_type": "Non-Industrial"}
    
    # slab calculation normally returns something different for 500k vs 1M.
    # In earlier turns we assumed it might change. Here mocked to 130.
    # Let's change mock to return different value if called with different SI?
    # Simple mock is fine for logic check.
    mock_terr_calc.side_effect = lambda occ, si: 65.0 if si == 500000.0 else 130.0
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorism_si=500000.0, # Less than building
        addOns=[AddOnItem(addOnCode="TERRORISM", sumInsured=500000.0)],
        risk_rate_per_mille=0.15
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # Basic: 1M * 0.15 = 150
    assert breakdown.basic_fire_premium == 150.0
    # Terrorism: 65 (for 500k)
    assert breakdown.terrorism_premium == 65.0
    assert breakdown.net_premium == 215.0

def test_policy_period_multiplier(mock_rates):
    """Verify Policy Multiplier applies to Net Premium"""
    mock_basic, mock_terr, mock_terr_calc, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True, "occupancy_type": "Non-Industrial"}

    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorism_si=1000000.0,
        addOns=[AddOnItem(addOnCode="TERRORISM", sumInsured=1000000.0)],
        policyPeriod=10, 
        risk_rate_per_mille=0.15
    )

    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']

    # Annual: Basic 150 + Terr 130 = 280
    # 10 Years: 2800
    assert breakdown.net_premium == 2800.0
    assert breakdown.basic_fire_premium == 1500.0
    assert breakdown.terrorism_premium == 1300.0
