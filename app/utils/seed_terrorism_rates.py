"""
Auto-seeding utility for fire_terrorism_rates table.
Runs on application startup to ensure table is populated with correct data.
"""

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Hardcoded seed data for terrorism rates - MUST BE 9 ROWS (3 occupancy types × 3 slabs each)
# Progressive slabs: each occupancy type has 3 tiers
TERRORISM_SEED_DATA = [
    # Residential (3 slabs)
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,  # 5 Billion
        "rate_per_mille": 0.07
    },
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 5000000000,
        "max_sum_insured": 10000000000,  # 10 Billion
        "rate_per_mille": 0.10
    },
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 10000000000,
        "max_sum_insured": None,  # Unlimited
        "rate_per_mille": 0.10
    },
    # Non-Industrial (3 slabs)
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,
        "rate_per_mille": 0.15
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 5000000000,
        "max_sum_insured": 10000000000,
        "rate_per_mille": 0.20
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 10000000000,
        "max_sum_insured": None,
        "rate_per_mille": 0.20
    },
    # Industrial (3 slabs)
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,
        "rate_per_mille": 0.20
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 5000000000,
        "max_sum_insured": 10000000000,
        "rate_per_mille": 0.25
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 10000000000,
        "max_sum_insured": None,
        "rate_per_mille": 0.25
    },
]

# Verify we have exactly 9 rows (3 occupancy types × 3 slabs)
assert len(TERRORISM_SEED_DATA) == 9, f"Expected 9 rows, got {len(TERRORISM_SEED_DATA)}"


def seed_fire_terrorism_rates(engine: Engine) -> None:
    """
    Auto-seed fire_terrorism_rates table with complete progressive slab data.
    
    This function:
    1. DELETES all existing rows from fire_terrorism_rates
    2. INSERTS the full 9-row dataset (3 occupancy types × 3 slabs each)
    3. Is idempotent (safe to run multiple times)
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        None
        
    Raises:
        Does not raise exceptions - logs errors instead to prevent app crash
    """
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Step 1: Check current row count
                count_query = text("SELECT COUNT(*) FROM fire_terrorism_rates")
                result = conn.execute(count_query)
                old_count = result.scalar()
                
                logger.info(f"🔄 Current fire_terrorism_rates rows: {old_count}")
                
                # Step 2: DELETE all existing rows
                delete_query = text("DELETE FROM fire_terrorism_rates")
                conn.execute(delete_query)
                logger.info(f"🗑️  Deleted {old_count} existing rows")
                
                # Step 3: INSERT all 9 rows
                insert_query = text("""
                    INSERT INTO fire_terrorism_rates 
                    (occupancy_type, min_sum_insured, max_sum_insured, rate_per_mille)
                    VALUES 
                    (:occupancy_type, :min_sum_insured, :max_sum_insured, :rate_per_mille)
                """)
                
                inserted_count = 0
                for row in TERRORISM_SEED_DATA:
                    conn.execute(insert_query, row)
                    inserted_count += 1
                    max_si_display = f"{row['max_sum_insured']:,}" if row['max_sum_insured'] else "Unlimited"
                    logger.info(
                        f"  ✓ [{inserted_count}] {row['occupancy_type']:15} | "
                        f"{row['min_sum_insured']:15,} - {max_si_display:15} | "
                        f"Rate: {row['rate_per_mille']}‰"
                    )
                
                # Step 4: Verify final count
                result = conn.execute(count_query)
                final_count = result.scalar()
                
                # Commit transaction
                trans.commit()
                
                logger.info(f"✅ Successfully seeded {final_count} terrorism rate slabs (Expected: {len(TERRORISM_SEED_DATA)})")
                
                if final_count != len(TERRORISM_SEED_DATA):
                    logger.error(f"❌ Row count mismatch! Expected {len(TERRORISM_SEED_DATA)}, got {final_count}")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Failed to seed terrorism rates: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Error in seed_fire_terrorism_rates: {e}")
        # Don't crash the app - just log the error
        # The startup validation will catch if rates are still missing
