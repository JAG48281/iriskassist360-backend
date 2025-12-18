"""
Auto-seeding utility for fire_terrorism_rates table.
Runs on application startup to ensure table is populated.
"""

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Hardcoded seed data for terrorism rates
TERRORISM_SEED_DATA = [
    # Residential
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,  # 5 Billion
        "rate_per_mille": 0.07
    },
    {
        "occupancy_type": "Residential",
        "min_sum_insured": 5000000000,
        "max_sum_insured": None,  # Unlimited
        "rate_per_mille": 0.10
    },
    # Non-Industrial
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,
        "rate_per_mille": 0.15
    },
    {
        "occupancy_type": "Non-Industrial",
        "min_sum_insured": 5000000000,
        "max_sum_insured": None,
        "rate_per_mille": 0.20
    },
    # Industrial
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 0,
        "max_sum_insured": 5000000000,
        "rate_per_mille": 0.20
    },
    {
        "occupancy_type": "Industrial",
        "min_sum_insured": 5000000000,
        "max_sum_insured": None,
        "rate_per_mille": 0.25
    },
]


def seed_fire_terrorism_rates(engine: Engine) -> None:
    """
    Auto-seed fire_terrorism_rates table if empty.
    
    This function:
    1. Checks if fire_terrorism_rates table is empty
    2. If empty, inserts hardcoded seed data
    3. If not empty, does nothing (idempotent)
    
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
                # Check if table is empty
                count_query = text("SELECT COUNT(*) FROM fire_terrorism_rates")
                result = conn.execute(count_query)
                count = result.scalar()
                
                if count > 0:
                    logger.info(f"✅ fire_terrorism_rates already populated ({count} rows) - skipping seed")
                    trans.rollback()
                    return
                
                logger.info("🌱 fire_terrorism_rates is empty - starting auto-seed...")
                
                # Insert seed data
                insert_query = text("""
                    INSERT INTO fire_terrorism_rates 
                    (occupancy_type, min_sum_insured, max_sum_insured, rate_per_mille)
                    VALUES 
                    (:occupancy_type, :min_sum_insured, :max_sum_insured, :rate_per_mille)
                """)
                
                for row in TERRORISM_SEED_DATA:
                    conn.execute(insert_query, row)
                    logger.info(
                        f"  ✓ Inserted: {row['occupancy_type']} | "
                        f"{row['min_sum_insured']:,} - "
                        f"{row['max_sum_insured'] if row['max_sum_insured'] else 'Unlimited'} | "
                        f"Rate: {row['rate_per_mille']}‰"
                    )
                
                # Commit transaction
                trans.commit()
                
                logger.info(f"✅ Successfully seeded {len(TERRORISM_SEED_DATA)} terrorism rate slabs")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Failed to seed terrorism rates: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Error in seed_fire_terrorism_rates: {e}")
        # Don't crash the app - just log the error
        # The startup validation will catch if rates are still missing
