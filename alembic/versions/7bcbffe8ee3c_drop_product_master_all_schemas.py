"""drop_product_master_all_schemas

Revision ID: 7bcbffe8ee3c
Revises: 95286d63da5c
Create Date: 2025-12-17 16:03:40

FINAL ERADICATION: Drop product_master BASE TABLE from ALL schemas.

ARCHITECTURAL LAW:
Products are LOGICAL, not relational.
product_master must not exist as a BASE TABLE in ANY schema.

This migration:
- Scans ALL user schemas (not just public)
- Drops product_master BASE TABLE wherever found
- Ignores system schemas (pg_catalog, information_schema, pg_toast)
- Uses CASCADE to drop dependencies
- Handles orphan tables, legacy artifacts, extension-created tables

WHY:
Previous migrations only dropped from public schema.
Tables could exist in other schemas (test, staging, dev, etc.)
This ensures complete eradication across entire database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bcbffe8ee3c'
down_revision: Union[str, None] = '95286d63da5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    FINAL ERADICATION: Drop product_master BASE TABLE from ALL schemas.
    
    Uses DO $$ block to:
    1. Query information_schema for ALL schemas containing product_master
    2. Dynamically drop the table from each schema
    3. Use CASCADE to handle dependencies
    
    Excludes system schemas:
    - pg_catalog
    - information_schema
    - pg_toast
    """
    print("\n" + "="*70)
    print("FINAL ERADICATION: product_master (ALL SCHEMAS)")
    print("="*70)
    print("\nScanning ALL schemas for product_master BASE TABLE...")
    
    op.execute("""
    DO $$
    DECLARE
        r RECORD;
        dropped_count INTEGER := 0;
    BEGIN
        -- Find all schemas containing product_master BASE TABLE
        FOR r IN
            SELECT table_schema
            FROM information_schema.tables
            WHERE table_name = 'product_master'
              AND table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        LOOP
            -- Drop the table from this schema
            EXECUTE format(
                'DROP TABLE IF EXISTS %I.product_master CASCADE',
                r.table_schema
            );
            
            dropped_count := dropped_count + 1;
            
            RAISE NOTICE '  ✅ Dropped product_master from schema: %', r.table_schema;
        END LOOP;
        
        IF dropped_count = 0 THEN
            RAISE NOTICE '  ℹ️  No product_master BASE TABLE found in any schema';
        ELSE
            RAISE NOTICE '  ✅ Total schemas cleaned: %', dropped_count;
        END IF;
    END
    $$;
    """)
    
    print("\n" + "="*70)
    print("FINAL ERADICATION COMPLETE")
    print("="*70)
    print("product_master BASE TABLE removed from ALL schemas")
    print("No table in public, no table anywhere")
    print("="*70 + "\n")


def downgrade() -> None:
    """
    No downgrade for final eradication.
    
    product_master is FORBIDDEN and shall never be recreated.
    This is the ultimate architectural enforcement.
    """
    print("⚠️  No downgrade available - product_master is FORBIDDEN FOREVER")
    pass
