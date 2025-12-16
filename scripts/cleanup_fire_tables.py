from sqlalchemy import create_engine, text, inspect
import sys
import os

# Add parent dir to path if needed for app imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def cleanup_fire_tables():
    # Tables explicitly listed to drop (plus normalized names based on inspection)
    tables_to_drop = [
        "product_basic_rates",
        "basic_fire_rates",
        "add_on_rates",
        "addon_rates",
        "pa_rates",
        "product_addon_group_map",
        "add_on_product_map", # Variant found
        "addon_groups",
        "stfi_rates",
        "stfi_rates_old",
        "eq_rates",
        "eq_rates_common",
        "eq_rates_bsus",
        "bsus_rates", # Variant found
        "eq_zone_rates",
        "eq_zones",
        "products_master", 
        "product_master" # Variant found
    ]

    # Tables to KEEP (Safety Check)
    tables_to_keep = [
        "occupancies",
        "terrorism_rates",
        "terrorism_slabs", # Real name
        "addons_master",
        "add_on_master" # Real name
    ]

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print("Starting Cleanup...")
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        for table in tables_to_drop:
            if table in existing_tables:
                print(f"Dropping table {table}...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            else:
                # print(f"Table {table} not found, skipping.")
                pass
                
    print("\nCleanup Complete.")
    
    # Verification
    final_inspector = inspect(engine)
    remaining = final_inspector.get_table_names()
    print("\nRemaining Tables:")
    for t in remaining:
        print(f"- {t}")

if __name__ == "__main__":
    cleanup_fire_tables()
