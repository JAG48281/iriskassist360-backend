"""align_fire_stfi_rates_column_naming

Revision ID: 7d0i1h2g4f5e
Revises: 6c9h0g1f3e4d
Create Date: 2025-12-17 15:20:00

CRITICAL: Align fire_stfi_rates column naming with other rate tables.

Issue:
- Table has column: stfi_rate_per_mille
- Seed script expects: rate_per_mille
- Other rate tables all use: rate_per_mille

This migration renames stfi_rate_per_mille → rate_per_mille for uniformity.

Design Rule: All rate tables must expose rate_per_mille.
Schema uniformity is mandatory for safe seeding and rating logic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d0i1h2g4f5e'
down_revision: Union[str, None] = '6c9h0g1f3e4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Rename stfi_rate_per_mille → rate_per_mille for schema uniformity.
    
    Before: fire_stfi_rates.stfi_rate_per_mille
    After:  fire_stfi_rates.rate_per_mille
    
    This aligns with:
    - fire_iib_rates.rate_per_mille
    - fire_bsus_rates.rate_per_mille
    - fire_eq_rates.rate_per_mille
    """
    print("\n" + "="*70)
    print("ALIGNING fire_stfi_rates COLUMN NAMING")
    print("="*70)
    print("\nRenaming stfi_rate_per_mille → rate_per_mille")
    print("Reason: Uniform naming across all rate tables")
    
    # Rename column for uniformity
    op.alter_column(
        table_name='fire_stfi_rates',
        column_name='stfi_rate_per_mille',
        new_column_name='rate_per_mille',
        type_=sa.Numeric(precision=10, scale=4),
        existing_type=sa.Numeric(precision=10, scale=4),
        existing_nullable=False
    )
    
    print("✅ Column renamed successfully")
    print("="*70 + "\n")


def downgrade() -> None:
    """
    Revert rate_per_mille → stfi_rate_per_mille.
    
    This restores the old naming if rollback is needed.
    """
    print("\n⚠️  Reverting fire_stfi_rates column naming")
    
    op.alter_column(
        table_name='fire_stfi_rates',
        column_name='rate_per_mille',
        new_column_name='stfi_rate_per_mille',
        type_=sa.Numeric(precision=10, scale=4),
        existing_type=sa.Numeric(precision=10, scale=4),
        existing_nullable=False
    )
    
    print("✅ Column reverted to stfi_rate_per_mille\n")
