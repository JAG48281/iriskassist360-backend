"""
Auto-seeding utility for fire_terrorism_rates table.
Runs on application startup to ensure table is populated with AUTHORITATIVE data.
"""

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# AUTHORITATIVE seed data for terrorism rates - MUST BE 13 ROWS
# Source: Official CSV data
# Residential: 2 slabs, Non-Industrial: 5 slabs, Industrial: 6 slabs
TERRORISM_SEED_DATA = [
    # Residential (2 slabs)
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 0,
        "max_sum_insured": 15000000000,  # 15 Billion
        "rate_per_mille": 0.07
    },
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 15000000001,
        "max_sum_insured": None,  # Unlimited (NULL)
        "rate_per_mille": 0.04
    },
    # Non-Industrial (5 slabs)
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 0,
        "max_sum_insured": 10000000000,  # 10 Billion
        "rate_per_mille": 0.13
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 10000000001,
        "max_sum_insured": 25000000000,  # 25 Billion
        "rate_per_mille": 0.11
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 25000000001,
        "max_sum_insured": 50000000000,  # 50 Billion
        "rate_per_mille": 0.09
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 50000000001,
        "max_sum_insured": 100000000000,  # 100 Billion
        "rate_per_mille": 0.07
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 100000000001,
        "max_sum_insured": None,  # Unlimited (NULL)
        "rate_per_mille": 0.05
    },
    # Industrial (6 slabs)
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,  # 5 Billion
        "rate_per_mille": 0.21
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 5000000001,
        "max_sum_insured": 15000000000,  # 15 Billion
        "rate_per_mille": 0.18
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 15000000001,
        "max_sum_insured": 25000000000,  # 25 Billion
        "rate_per_mille": 0.13
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 25000000001,
        "max_sum_insured": 50000000000,  # 50 Billion
        "rate_per_mille": 0.09
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 50000000001,
        "max_sum_insured": 100000000000,  # 100 Billion
        "rate_per_mille": 0.07
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 100000000001,
        "max_sum_insured": None,  # Unlimited (NULL)
        "rate_per_mille": 0.05
    },
]

# Verify we have exactly 13 rows (2 + 5 + 6)
assert len(TERRORISM_SEED_DATA) == 13, f"Expected 13 rows, got {len(TERRORISM_SEED_DATA)}"


def seed_fire_terrorism_rates(engine: Engine) -> None:
    """
    Auto-seed fire_terrorism_rates table with AUTHORITATIVE progressive slab data.
    
    This function:
    1. TRUNCATES fire_terrorism_rates table
    2. INSERTS the full 13-row authoritative dataset
    3. Verifies row counts per occupancy type
    4. Is idempotent (safe to run multiple times)
    
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
                
                # Step 2: TRUNCATE table (faster than DELETE for full table clear)
                truncate_query = text("TRUNCATE TABLE fire_terrorism_rates")
                conn.execute(truncate_query)
                logger.info(f"🗑️  Truncated fire_terrorism_rates table")
                
                # Step 3: INSERT all 13 rows
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
                    max_si_display = f"{row['max_sum_insured']:,}" if row['max_sum_insured'] else "NULL (Unlimited)"
                    logger.info(
                        f"  ✓ [{inserted_count:2d}] {row['occupancy_type']:15} | "
                        f"{row['min_sum_insured']:15,} - {max_si_display:20} | "
                        f"Rate: {row['rate_per_mille']}‰"
                    )
                
                # Step 4: Verify final count per occupancy type
                verify_query = text("""
                    SELECT occupancy_type, COUNT(*) as count
                    FROM fire_terrorism_rates
                    GROUP BY occupancy_type
                    ORDER BY occupancy_type
                """)
                result = conn.execute(verify_query)
                rows = result.fetchall()
                
                logger.info(f"\n📊 Row counts by occupancy type:")
                total_count = 0
                for row in rows:
                    logger.info(f"  {row.occupancy_type:15} = {row.count} rows")
                    total_count += row.count
                
                # Commit transaction
                trans.commit()
                
                logger.info(f"\n✅ Successfully seeded {total_count} terrorism rate slabs")
                logger.info(f"   Expected: Residential=2, Non-Industrial=5, Industrial=6, Total=13")
                
                if total_count != 13:
                    logger.error(f"❌ Row count mismatch! Expected 13, got {total_count}")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Failed to seed terrorism rates: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Error in seed_fire_terrorism_rates: {e}")
        # Don't crash the app - just log the error
        # The startup validation will catch if rates are still missing
