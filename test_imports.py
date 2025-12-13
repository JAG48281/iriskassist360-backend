import sys
import os
sys.path.append(os.getcwd())

# Test imports
try:
    print("Testing imports...")
    from app.schemas.fire_premium import UBGRUVGRRequest, UBGRUVGRResponse
    print("✅ Schemas imported")
    
    from app.services.fire_premium_service import FirePremiumCalculator
    print("✅ Service imported")
    
    from app.routers.fire import fire_premium
    print("✅ Router imported")
    
    print("\n✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
