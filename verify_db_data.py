"""
Quick verification script to check if risk rate data exists in the database.
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment (use project default)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Uiic%40151000@localhost:5432/iriskassist360_db")


def check_data():
    """Check if we have the necessary data in the database"""
    engine = create_engine(DATABASE_URL)
    
    print("="*80)
    print("DATABASE VERIFICATION")
    print("="*80)
    
    with engine.connect() as conn:
        # Check occupancies
        print("\n1. Checking occupancies table...")
        result = conn.execute(text("SELECT COUNT(*) as count FROM occupancies")).fetchone()
        print(f"   Total occupancies: {result.count}")
        
        if result.count > 0:
            sample = conn.execute(text("""
                SELECT id, iib_code, occupancy_type, section_aift 
                FROM occupancies 
                WHERE iib_code IN ('1001', '1001_2', '2001')
                LIMIT 5
            """)).fetchall()
            
            print(f"\n   Sample occupancies:")
            for row in sample:
                print(f"   - ID={row.id}, IIB={row.iib_code}, Type={row.occupancy_type}, Section={row.section_aift}")
        
        # Check product_basic_rates
        print("\n2. Checking product_basic_rates table...")
        result = conn.execute(text("SELECT COUNT(*) as count FROM product_basic_rates")).fetchone()
        print(f"   Total rates: {result.count}")
        
        if result.count > 0:
            sample = conn.execute(text("""
                SELECT pbr.id, pbr.product_code, pbr.occupancy_id, pbr.basic_rate,
                       o.iib_code, o.occupancy_type
                FROM product_basic_rates pbr
                JOIN occupancies o ON pbr.occupancy_id = o.id
                WHERE pbr.product_code IN ('UBGR', 'BGRP', 'UVGR', 'UVGS')
                LIMIT 10
            """)).fetchall()
            
            print(f"\n   Sample rates:")
            for row in sample:
                print(f"   - {row.product_code} + Occ#{row.occupancy_id} ({row.iib_code}/{row.occupancy_type}) = {row.basic_rate}‰")
        
        # Check for UBGR/BGRP rates specifically
        print("\n3. Checking UBGR/BGRP rates for occupancy 1001...")
        result = conn.execute(text("""
            SELECT pbr.product_code, pbr.basic_rate, o.iib_code, o.occupancy_type
            FROM product_basic_rates pbr
            JOIN occupancies o ON pbr.occupancy_id = o.id
            WHERE pbr.product_code IN ('UBGR', 'BGRP')
              AND o.iib_code = '1001'
        """)).fetchall()
        
        if result:
            print(f"   ✅ Found {len(result)} rate(s):")
            for row in result:
                print(f"   - {row.product_code} + {row.iib_code} ({row.occupancy_type}) = {row.basic_rate}‰")
        else:
            print(f"   ❌ NO RATES FOUND for UBGR/BGRP + 1001")
            print(f"   This is the root cause of the issue!")
            
        # Check terrorism_slabs
        print("\n4. Checking terrorism_slabs table...")
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM terrorism_slabs 
            WHERE product_code IN ('UBGR', 'BGRP')
        """)).fetchone()
        print(f"   Terrorism slabs for UBGR/BGRP: {result.count}")
        
    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        check_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
