import sys
import os
sys.path.append(os.getcwd())
from app.services.rating_engine import get_terrorism_rate_per_mille

try:
    rate = float(get_terrorism_rate_per_mille("BGRP", occupancy_code="1001", tsi=10000000.0))
    print(f"BGRP Rate: {rate}")
    if abs(rate - 0.07) < 0.00001:
        print("✅ VERIFIED: Rate is 0.07")
    else:
        print(f"❌ FAILED: Rate is {rate}")
except Exception as e:
    print(f"EXCEPTION: {e}")
