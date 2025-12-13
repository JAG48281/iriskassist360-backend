import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def check_ubgr_rates():
    with engine.connect() as conn:
        # Check Product Master for UBGR
        print("--- Checking Product Master ---")
        result = conn.execute(text("SELECT id, product_code, product_name FROM product_master WHERE product_code IN ('UBGR', 'BGRP')"))
        products = result.fetchall()
        for p in products:
            print(p)
            
        product_codes = [p.product_code for p in products]
        
        # Check Occupancies for 1001, 1001_2
        print("\n--- Checking Occupancies ---")
        result = conn.execute(text("SELECT id, iib_code, risk_description FROM occupancies WHERE iib_code IN ('1001', '1001_2')"))
        occupancies = result.fetchall()
        for o in occupancies:
            print(o)
            
        if not products or not occupancies:
            print("Missing Product or Occupancies")
            return

        # Check Rates
        print("\n--- Checking Product Basic Rates ---")
        result = conn.execute(text("""
            SELECT r.id, p.product_code, o.iib_code, r.basic_rate 
            FROM product_basic_rates r
            JOIN product_master p ON r.product_id = p.id
            JOIN occupancies o ON r.occupancy_id = o.id
            WHERE p.product_code IN ('UBGR', 'BGRP')
            AND o.iib_code IN ('1001', '1001_2')
        """))
        rates = result.fetchall()
        for r in rates:
            print(r)

if __name__ == "__main__":
    check_ubgr_rates()
