import sys
import os
sys.path.append(os.getcwd())

from app.schemas.fire_premium import UBGRUVGRRequest, PASelection, AddOnItem
from app.services.fire_premium_service import FirePremiumCalculator

# Create a test request
request = UBGRUVGRRequest(
    productCode="UBGR",
    occupancyCode="1001",
    buildingSI=1000000,
    contentsSI=200000,
    addOns=[],
    paSelection=PASelection(proposer=False, spouse=False),
    discountPercentage=0,
    loadingPercentage=0
)

print("Testing UBGR Premium Calculation...")
print(f"Request: {request.dict()}")

try:
    breakdown = FirePremiumCalculator.calculate_ubgr_uvgr(request)
    print("\n✅ Calculation successful!")
    print(f"\nBreakdown:")
    print(f"  Basic Fire Premium: {breakdown.basicFirePremium}")
    print(f"  Add-On Premium: {breakdown.addOnPremium}")
    print(f"  Discount Amount: {breakdown.discountAmount}")
    print(f"  Subtotal: {breakdown.subtotal}")
    print(f"  Loading Amount: {breakdown.loadingAmount}")
    print(f"  Terrorism Premium: {breakdown.terrorismPremium}")
    print(f"  Net Premium: {breakdown.netPremium}")
    print(f"  Gross Premium: {breakdown.grossPremium}")
except Exception as e:
    print(f"\n❌ Calculation failed: {e}")
    import traceback
    traceback.print_exc()
