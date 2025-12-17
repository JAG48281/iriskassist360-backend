"""
Simple test to verify fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Get first UBGR occupancy
    occ = conn.execute(
        text("SELECT id, iib_code FROM occupancies WHERE iib_code = '1001' LIMIT 1")
    ).fetchone()
    
    if occ:
        print(f"Occupancy ID: {occ.id}, IIB Code: {occ.iib_code}")
        
        # Get rate
        rate = conn.execute(
            text("SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :iib"),
            {"iib": occ.iib_code}
        ).scalar()
        
        print(f"Risk Rate: {rate}‰")
        print("✅ Test PASSED" if rate else "❌ Test FAILED")
    else:
        print("❌ No UBGR occupancy found")
