
import pytest
from decimal import Decimal
from app.services.fire_premium_service import FirePremiumCalculator
from app.schemas.fire_premium import UBGRUVGRRequest, PASelection, AddOnItem

# Mock external dependencies if needed, or use integration style if DB is available.
# Since this logic calls DB functions (get_basic_rate_per_mille), we might need to mock them.
from unittest.mock import patch

@pytest.fixture
def mock_rates():
    with patch('app.services.fire_premium_service.get_basic_rate_per_mille') as mock_basic, \
         patch('app.services.fire_premium_service.get_terrorism_rate_per_mille') as mock_terr, \
         patch('app.services.fire_premium_service.get_occupancy_details') as mock_occ, \
         patch('app.services.fire_premium_service.get_add_on_rate') as mock_addon:
        
        mock_basic.return_value = Decimal("0.15") # 0.15 per mille
        yield mock_basic, mock_terr, mock_occ, mock_addon

def test_ubgr_calculation_standard(mock_rates):
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        contentsSI=500000.0, # Total 1.5M
        terrorismSI=1500000.0,
        discountPercentage=0,
        loadingPercentage=0
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # 1.5M * 0.15 / 1000 = 225
    assert breakdown.basic_premium == 225.0
    
    # Terrorism: 1.5M * 0.07 / 1000 = 105
    assert breakdown.terrorism_premium == 105.0
    
    # Net: 225 + 105 = 330
    assert breakdown.net_premium == 330.0

def test_uvgr_calculation_no_terrorism(mock_rates):
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True}
    # Should not call get_terrorism_rate_per_mille or ignore it
    
    request = UBGRUVGRRequest(
        productCode="UVGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        contentsSI=0,
        terrorismSI=0,
        discountPercentage=0,
        loadingPercentage=0
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # 1M * 0.15 / 1000 = 150
    assert breakdown.basic_premium == 150.0
    
    # Terrorism must be 0
    assert breakdown.terrorism_premium == 0.0 or breakdown.terrorism_premium is None
    
    # Net: 150
    assert breakdown.net_premium == 150.0

def test_loading_logic(mock_rates):
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        discountPercentage=0,
        loadingPercentage=10, # 10% loading
        terrorismSI=1000000.0
    )
    
    # Basic: 150
    # Addon: 0
    # Subtotal: 150
    # Loading: 150 * 10% = 15
    # Terrorism: 1M * 0.07/1000 = 70
    # Net: 150 + 15 + 70 = 235
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    assert breakdown.basic_premium == 150.0
    assert breakdown.loading_amount == 15.0
    assert breakdown.terrorism_premium == 70.0
    assert breakdown.net_premium == 235.0

def test_discount_logic(mock_rates):
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        discountPercentage=10, # 10% discount
        loadingPercentage=0,
        terrorismSI=1000000.0
    )
    
    # Basic: 150
    # Discount: 150 * 10% = 15
    # Subtotal: 135
    # Loading: 0
    # Terrorism: 1M * 0.07 / 1000 = 70
    # Net: 135 + 70 = 205
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    assert breakdown.discount_amount == 15.0
    assert breakdown.sub_total == 135.0
    assert breakdown.net_premium == 205.0

def test_uvgr_with_addons_and_discount(mock_rates):
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": True}
    # Mock add-on rate: per_mille, 5.0
    mock_addon.return_value = ("per_mille", Decimal("5.0"))
    
    request = UBGRUVGRRequest(
        productCode="UVGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        discountPercentage=10, 
        loadingPercentage=0,
        addOns=[AddOnItem(addOnCode="ADD1", sumInsured=100000.0)],
        terrorismSI=0
    )
    
    # Basic: 1M * 0.15/1000 = 150
    # Addon: 100k * 5.0/1000 = 500
    # Discount Base: 150 + 500= 650
    # Discount: 650 * 10% = 65.0
    # Subtotal: 650 - 65 = 585.0
    # Net: 585.0 (UVGR -> No Terrorism)
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    assert breakdown.basic_premium == 150.0
    assert breakdown.add_on_premium == 500.0
    assert breakdown.discount_amount == 65.0
    assert breakdown.sub_total == 585.0
    assert breakdown.net_premium == 585.0

def test_addons_disabled_integration(mock_rates):
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_occ.return_value = {"allow_addons": False} # Disabled logic
    mock_addon.return_value = ("per_mille", Decimal("5.0"))
    
    request = UBGRUVGRRequest(
        productCode="UVGR",
        occupancyCode="RESTRICTED",
        buildingSI=1000000.0,
        addOns=[AddOnItem(addOnCode="ADD1", sumInsured=100000.0)],
        terrorismSI=0
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # Addon should be 0 despite request
    assert breakdown.add_on_premium == 0.0
    assert breakdown.basic_premium == 150.0

def test_terrorism_si_isolation(mock_rates):
    """Verify terrorism is calculated on terrorismSI, not BuildingSI"""
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}
    
    building_si = 1000000.0
    terr_si = 500000.0 # Different from Building SI
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=building_si,
        contentsSI=0,
        terrorismSI=terr_si,
        discountPercentage=0,
        loadingPercentage=0
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # Basic: 1M * 0.15 = 150
    assert breakdown.basic_premium == 150.0
    
    # Terrorism: 500k * 0.07 / 1000 = 35.0 (NOT 70.0)
    assert breakdown.terrorism_premium == 35.0

def test_zero_terrorism_si(mock_rates):
    """Verify 0 Terrorism SI results in 0 Terrorism Premium"""
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorismSI=0, # ZERO
        discountPercentage=0,
        loadingPercentage=0
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    assert breakdown.basic_premium == 150.0
    assert breakdown.terrorism_premium == 0.0

def test_policy_period_multiplier(mock_rates):
    """Verify Policy Multiplier applies to Net Premium"""
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}
    
    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorismSI=1000000.0,
        discountPercentage=0,
        loadingPercentage=0,
        policyPeriod=10 # 10 Years
    )
    
    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']
    
    # Annual Calculation:
    # Basic = 150
    # Terrorism = 70
    # Annual Net = 220
    
    # Multiplier: 220 * 10 = 2200
    assert breakdown.net_premium == 2200.0
    
    # Tax on 2200
    assert breakdown.cgst == 198.0
    assert breakdown.gross_premium == 2200 + 198 + 198 + 1.0 # 2597

def test_terrorism_isolation_with_discount_and_loading(mock_rates):
    """
    STRICTLY verify that Terrorism Premium is TOTALLY UNAFFECTED by Discount and Loading.
    """
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}

    request = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorismSI=1000000.0,
        discountPercentage=10, # 10% Discount
        loadingPercentage=10,  # 10% Loading
        policyPeriod=1
    )

    result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    breakdown = result['breakdown']

    # 1. Basic: 1M * 0.15 / 1000 = 150.0
    assert breakdown.basic_premium == 150.0

    # 2. Discount is 10% of Basic (150) = 15.0
    assert breakdown.discount_amount == 15.0

    # 3. Subtotal = 150 - 15 = 135.0
    assert breakdown.sub_total == 135.0

    # 4. Loading is 10% of Subtotal (135) = 13.5
    assert breakdown.loading_amount == 13.5

    # 5. Terrorism: 1M * 0.07 / 1000 = 70.0 (MUST BE PURE)
    # CRITICAL: If discount applied, it would be 63. If loading applied, it would vary.
    # It MUST be exactly 70.0.
    assert breakdown.terrorism_premium == 70.0

    # 6. Net: 135 (Sub) + 13.5 (Load) + 70 (Terr) = 218.5
    assert breakdown.net_premium == 218.5

def test_policy_period_scales_net_premium_only(mock_rates):
    """
    Verify that policy period multiplier:
    1. Scales net premium correctly
    2. GST is calculated on scaled net premium
    3. Stamp duty does NOT scale
    """
    mock_basic, mock_terr, mock_occ, mock_addon = mock_rates
    mock_terr.return_value = Decimal("0.07")
    mock_occ.return_value = {"allow_addons": True}

    # Test 1-year policy
    request_1yr = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorismSI=1000000.0,
        discountPercentage=0,
        loadingPercentage=0,
        policyPeriod=1
    )

    result_1yr = FirePremiumCalculator.calculate_ubgr_uvgr(request_1yr)
    breakdown_1yr = result_1yr['breakdown']

    # Test 3-year policy
    request_3yr = UBGRUVGRRequest(
        productCode="UBGR",
        occupancyCode="1001",
        buildingSI=1000000.0,
        terrorismSI=1000000.0,
        discountPercentage=0,
        loadingPercentage=0,
        policyPeriod=3
    )

    result_3yr = FirePremiumCalculator.calculate_ubgr_uvgr(request_3yr)
    breakdown_3yr = result_3yr['breakdown']

    # Annual calculation:
    # Basic: 150, Terrorism: 70, Annual Net: 220

    # 1-year policy
    assert breakdown_1yr.net_premium == 220.0
    assert breakdown_1yr.cgst == 19.8  # 220 * 0.09
    assert breakdown_1yr.sgst == 19.8
    assert breakdown_1yr.stamp_duty == 1.0
    assert breakdown_1yr.gross_premium == 220.0 + 19.8 + 19.8 + 1.0  # 260.6

    # 3-year policy
    assert breakdown_3yr.net_premium == 660.0  # 220 * 3
    assert breakdown_3yr.cgst == 59.4  # 660 * 0.09 (GST scales with net)
    assert breakdown_3yr.sgst == 59.4
    assert breakdown_3yr.stamp_duty == 1.0  # FIXED, does NOT scale
    assert breakdown_3yr.gross_premium == 660.0 + 59.4 + 59.4 + 1.0  # 779.8

    # Verify scaling relationship
    assert breakdown_3yr.net_premium == pytest.approx(breakdown_1yr.net_premium * 3)
    assert breakdown_3yr.cgst == pytest.approx(breakdown_1yr.cgst * 3)
    assert breakdown_3yr.stamp_duty == breakdown_1yr.stamp_duty  # NO scaling


