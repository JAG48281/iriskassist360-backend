"""nuke_product_master_everywhere

Revision ID: 95286d63da5c
Revises: 7d0i1h2g4f5e
Create Date: 2025-12-17 15:52:17.664977

NUCLEAR CLEANUP: Remove product_master in ALL forms (table, view, materialized view).

ARCHITECTURAL LAW:
Products are LOGICAL, not relational.
product_master must not exist as ANY database object.

This migration handles:
- BASE TABLE
- VIEW
- MATERIALIZED VIEW
- Any other relation that might cause false positives

WHY:
to_regclass() detects ANY relation type (views, tables, etc.)
This was causing false positives when views existed
We need to guarantee ZERO product_master objects of ANY type
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95286d63da5c'
down_revision: Union[str, None] = '7d0i1h2g4f5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    NUCLEAR CLEANUP: Drop product_master in ALL forms.
    
    Handles:
    - TABLE (base tables)
    - VIEW (views)
    - MATERIALIZED VIEW (materialized views)
    
    Uses CASCADE to drop any dependent objects.
    Uses IF EXISTS to avoid errors if object doesn't exist.
    """
    print("\n" + "="*70)
    print("NUCLEAR CLEANUP: product_master")
    print("="*70)
    print("\nRemoving product_master in ALL forms (table, view, materialized view)...")
    
    # Drop table if exists
    print("  Checking for BASE TABLE...")
    op.execute("DROP TABLE IF EXISTS product_master CASCADE")
    print("  ✅ Dropped TABLE (if existed)")
    
    # Drop view if exists
    print("  Checking for VIEW...")
    op.execute("DROP VIEW IF EXISTS product_master CASCADE")
    print("  ✅ Dropped VIEW (if existed)")
    
    # Drop materialized view if exists
    print("  Checking for MATERIALIZED VIEW...")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS product_master CASCADE")
    print("  ✅ Dropped MATERIALIZED VIEW (if existed)")
    
    print("\n" + "="*70)
    print("NUCLEAR CLEANUP COMPLETE")
    print("="*70)
    print("product_master eradicated in ALL forms")
    print("No table, no view, no materialized view")
    print("="*70 + "\n")


def downgrade() -> None:
    """
    No downgrade for nuclear cleanup.
    
    product_master is FORBIDDEN and should never be recreated.
    This is a one-way architectural enforcement.
    """
    print("⚠️  No downgrade available - product_master is FORBIDDEN")
    pass

