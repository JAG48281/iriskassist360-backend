"""
Test script to validate policy period string parsing.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.fire_premium import UBGRUVGRRequest, PASelection


def test_policy_period_parsing():
    """Test that policy period strings are correctly parsed"""
    
    print("\n" + "="*70)
    print("POLICY PERIOD STRING PARSING TEST")
    print("="*70)
    
    test_cases = [
        ("1 Year", 1),
        ("2 Years", 2),
        ("3 Years", 3),
        ("4 Years", 4),
        ("10 Years", 10),
        (1, 1),  # Integer input
        (5, 5),  # Integer input
    ]
    
    all_passed = True
    
    for input_value, expected in test_cases:
        try:
            request = UBGRUVGRRequest(
                productCode="UBGR",
                occupancyCode="1001",
                buildingSI=1000000.0,
                policyPeriod=input_value,
                risk_rate_per_mille=0.15
            )
            
            actual = request.policyPeriod
            status = "PASS" if actual == expected else "FAIL"
            
            print(f"\n{status} | Input: {repr(input_value):15} -> Parsed: {actual} (Expected: {expected})")
            
            if actual != expected:
                all_passed = False
                
        except Exception as e:
            print(f"\nFAIL | Input: {repr(input_value):15} -> ERROR: {e}")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("ALL TESTS PASSED - Policy period parsing works correctly!")
    else:
        print("SOME TESTS FAILED - Please review the validator logic")
    print("="*70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = test_policy_period_parsing()
    sys.exit(0 if success else 1)
