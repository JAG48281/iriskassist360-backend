
import sys
try:
    from app.services.fire_premium_service import FirePremiumCalculator
    print("Syntax OK")
except Exception as e:
    print(e)
