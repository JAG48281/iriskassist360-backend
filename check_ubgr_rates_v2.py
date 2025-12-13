import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.getcwd())
from app.database import engine

def check_rates():
    with engine.connect() as conn:
        print("Checking Products...")
        products = conn.execute(text("SELECT product_code FROM product_master WHERE product_code IN ('UBGR', 'BGRP')")).fetchall()
        print(f"Products found: {[p.product_code for p in products]}")
        
        print("\nChecking Rates for BGRP/UBGR for 1001/1001_2:")
        query = text("""
            SELECT p.product_code, o.iib_code, r.basic_rate 
            FROM product_basic_rates r
            JOIN product_master p ON r.product_id = p.id
            JOIN occupancies o ON r.occupancy_id = o.id
            WHERE p.product_code IN ('UBGR', 'BGRP')
            AND o.iib_code IN ('1001', '1001_2')
        """)
        rates = conn.execute(query).fetchall()
        if not rates:
            print("No rates found.")
        for r in rates:
            print(f"Product: {r.product_code}, IIB: {r.iib_code}, Rate: {r.basic_rate}")

if __name__ == "__main__":
    check_rates()
