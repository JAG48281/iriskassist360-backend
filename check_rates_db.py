"""
Check if product_basic_rates table has data for UBGR/BGRP products.
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Uiic%40151000@localhost:5432/iriskassist360_db")

def check_rates():
    engine = create_engine(DATABASE_URL)
    
    print("="*80)
    print("CHECKING PRODUCT_BASIC_RATES TABLE")
    print("="*80)
    
    with engine.connect() as conn:
        # Check if table exists
        print("\n1. Checking if product_basic_rates table exists...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'product_basic_rates'
            )
        """)).scalar()
        
        if not result:
            print("   ❌ Table 'product_basic_rates' does not exist!")
            return False
        
        print("   ✅ Table exists")
        
        # Check total count
        print("\n2. Checking total rates...")
        count = conn.execute(text("SELECT COUNT(*) FROM product_basic_rates")).scalar()
        print(f"   Total rates in table: {count}")
        
        if count == 0:
            print("   ❌ No rates found in product_basic_rates table!")
            print("\n   ACTION REQUIRED:")
            print("   Run: python seed.py")
            print("   Or manually insert rates into product_basic_rates table")
            return False
        
        # Check for UBGR/BGRP rates with occupancy 1001
        print("\n3. Checking UBGR/BGRP rates for occupancy 1001...")
        result = conn.execute(text("""
            SELECT 
                pbr.product_code,
                pbr.occupancy_id,
                pbr.basic_rate,
                o.iib_code,
                o.occupancy_type
            FROM product_basic_rates pbr
            JOIN occupancies o ON pbr.occupancy_id = o.id
            WHERE pbr.product_code IN ('UBGR', 'BGRP', 'UVGR', 'UVGS')
              AND o.iib_code = '1001'
            ORDER BY pbr.product_code
        """)).fetchall()
        
        if not result:
            print("   ❌ No rates found for UBGR/BGRP/UVGR/UVGS + occupancy 1001!")
            print("\n   Current rates in table:")
            
            all_rates = conn.execute(text("""
                SELECT 
                    pbr.product_code,
                    pbr.occupancy_id,
                    pbr.basic_rate,
                    o.iib_code
                FROM product_basic_rates pbr
                LEFT JOIN occupancies o ON pbr.occupancy_id = o.id
                LIMIT 10
            """)).fetchall()
            
            for row in all_rates:
                print(f"   - {row.product_code} + Occ#{row.occupancy_id} ({row.iib_code}) = {row.basic_rate}‰")
            
            print("\n   ACTION REQUIRED:")
            print("   Insert rates for UBGR/BGRP/UVGR/UVGS with occupancy_id for iib_code='1001'")
            return False
        
        print(f"   ✅ Found {len(result)} rate(s):")
        for row in result:
            print(f"   - {row.product_code} + Occ#{row.occupancy_id} ({row.iib_code}/{row.occupancy_type}) = {row.basic_rate}‰")
        
        # Check occupancy 1001 exists
        print("\n4. Checking occupancy 1001...")
        occ = conn.execute(text("""
            SELECT id, iib_code, occupancy_type, section_aift
            FROM occupancies
            WHERE iib_code = '1001'
        """)).fetchone()
        
        if not occ:
            print("   ❌ Occupancy 1001 not found in occupancies table!")
            return False
        
        print(f"   ✅ Occupancy found: ID={occ.id}, Type={occ.occupancy_type}, Section={occ.section_aift}")
        
        print("\n" + "="*80)
        print("✅ DATABASE CHECK PASSED")
        print("="*80)
        print("\nAll required data is present:")
        print(f"✓ product_basic_rates table exists with {count} rates")
        print(f"✓ Rates configured for Fire products + occupancy 1001")
        print(f"✓ Occupancy 1001 exists (ID={occ.id})")
        print("\nRisk rate resolution should work correctly!")
        print("="*80)
        
        return True

if __name__ == "__main__":
    try:
        success = check_rates()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
