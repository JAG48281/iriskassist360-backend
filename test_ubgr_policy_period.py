"""
Test script to validate UBGR policy period scaling.

Validates that Net Premium scales linearly with Policy Period:
- 1 Year: Net = 600
- 2 Years: Net = 1200
- 3 Years: Net = 1800

For SI = 40,00,000 and Rate = 0.15 per mille
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.fire_premium_service import FirePremiumCalculator
from app.schemas.fire_premium import UBGRUVGRRequest, PASelection
from unittest.mock import patch
from decimal import Decimal


def mock_get_terrorism_rate(*args, **kwargs):
    """Mock terrorism rate - return 0 for this test"""
    return Decimal("0")


def mock_calculate_terrorism_premium(*args, **kwargs):
    """Mock terrorism premium - return 0 for this test"""
    return 0.0


def mock_get_occupancy_details(*args, **kwargs):
    """Mock occupancy details"""
    return {"allow_addons": True, "occupancy_type": "Non-Industrial"}


def test_ubgr_policy_period_scaling():
    """Test UBGR premium calculation with different policy periods"""
    
    print("\n" + "="*70)
    print("UBGR POLICY PERIOD SCALING VALIDATION")
    print("="*70)
    print(f"\nTest Parameters:")
    print(f"  Sum Insured: Rs 40,00,000")
    print(f"  Risk Rate: 0.15 per mille")
    print(f"  Product: UBGR")
    print(f"  Expected Annual Net Premium: Rs 600")
    print("\n" + "-"*70)
    
    # Mock external dependencies
    with patch('app.services.fire_premium_service.get_terrorism_rate_per_mille', mock_get_terrorism_rate), \
         patch('app.services.fire_premium_service.calculate_terrorism_premium', mock_calculate_terrorism_premium), \
         patch('app.services.fire_premium_service.get_occupancy_details', mock_get_occupancy_details):
        
        test_cases = [
            (1, 600.0),
            (2, 1200.0),
            (3, 1800.0)
        ]
        
        all_passed = True
        
        for policy_period, expected_net in test_cases:
            # Create request
            request = UBGRUVGRRequest(
                productCode="UBGR",
                occupancyCode="1001",
                buildingSI=4000000.0,
                contentsSI=0,
                terrorismSI=0,  # No terrorism for this test
                risk_rate_per_mille=0.15,
                policyPeriod=policy_period,
                paSelection=PASelection(proposer=False, spouse=False),
                discountPercentage=0,
                loadingPercentage=0
            )
            
            # Calculate
            result = FirePremiumCalculator.calculate_ubgr_uvgr(request)
            breakdown = result['breakdown']
            meta = result['meta']
            
            # Validate
            basic_fire = breakdown.basic_fire_premium
            fire_subtotal = breakdown.fire_subtotal
            net_premium = breakdown.net_premium
            policy_years = meta.policy_period_years
            
            # Check basic fire (should scale with period)
            expected_basic = 600.0 * policy_period
            basic_match = abs(basic_fire - expected_basic) < 0.01
            
            # Check multi-year net
            expected_net = 600.0 * policy_period
            net_match = abs(net_premium - expected_net) < 0.01
            
            # Check policy period
            period_match = policy_years == policy_period
            
            # Calculate expected CGST/SGST (9% each on net premium)
            expected_cgst = expected_net * 0.09
            expected_sgst = expected_net * 0.09
            expected_gross = expected_net + expected_cgst + expected_sgst + 1.0  # +1 for stamp duty
            
            cgst_match = abs(breakdown.cgst - expected_cgst) < 0.01
            sgst_match = abs(breakdown.sgst - expected_sgst) < 0.01
            gross_match = abs(breakdown.gross_premium - expected_gross) < 0.01
            
            # Print results
            status = "PASS" if (basic_match and net_match and period_match and cgst_match and sgst_match and gross_match) else "FAIL"
            print(f"\n{status} | Policy Period: {policy_period} Year(s)")
            print(f"  Basic Fire Premium: Rs {basic_fire:.2f} (Expected: Rs {expected_basic:.2f}) {'OK' if basic_match else 'FAIL'}")
            print(f"  Fire Subtotal: Rs {fire_subtotal:.2f}")
            print(f"  Net Premium: Rs {net_premium:.2f} (Expected: Rs {expected_net:.2f}) {'OK' if net_match else 'FAIL'}")
            print(f"  Policy Period Years: {policy_years} (Expected: {policy_period}) {'OK' if period_match else 'FAIL'}")
            print(f"  CGST (9%): Rs {breakdown.cgst:.2f} (Expected: Rs {expected_cgst:.2f}) {'OK' if cgst_match else 'FAIL'}")
            print(f"  SGST (9%): Rs {breakdown.sgst:.2f} (Expected: Rs {expected_sgst:.2f}) {'OK' if sgst_match else 'FAIL'}")
            print(f"  Stamp Duty: Rs {breakdown.stamp_duty:.2f} (Fixed, no scaling)")
            print(f"  Gross Premium: Rs {breakdown.gross_premium:.2f} (Expected: Rs {expected_gross:.2f}) {'OK' if gross_match else 'FAIL'}")
            
            if not (basic_match and net_match and period_match and cgst_match and sgst_match and gross_match):
                all_passed = False
        
        print("\n" + "="*70)
        if all_passed:
            print("ALL TESTS PASSED - Policy period scaling is correct!")
        else:
            print("SOME TESTS FAILED - Please review the calculation logic")
        print("="*70 + "\n")
        
        return all_passed


if __name__ == "__main__":
    success = test_ubgr_policy_period_scaling()
    sys.exit(0 if success else 1)
