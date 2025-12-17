"""remove_legacy_duplicate_rate_tables

Revision ID: 5b8g9f0e2d3c
Revises: 4a7f8e9d1c2b
Create Date: 2025-12-17 15:00:00

CRITICAL: Removes legacy/duplicate rate tables that are not used by backend.
These tables are remnants of earlier schema versions and should be empty.

Legacy tables to remove:
- eq_rates (replaced by fire_eq_rates)
- stfi_rates (replaced by fire_stfi_rates)
- bsus_rates (replaced by fire_bsus_rates)
- generic_rates (never used)

Safety: Only drops if tables exist (IF EXISTS clause).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '5b8g9f0e2d3c'
down_revision: Union[str, None] = '4a7f8e9d1c2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Safely remove legacy/duplicate rate tables.
    
    These tables are not referenced in backend code and should be empty.
    Uses IF EXISTS for safety in case tables were already dropped.
    """
    # Get connection to check if tables are empty
    conn = op.get_bind()
    
    legacy_tables = ['eq_rates', 'stfi_rates', 'bsus_rates', 'generic_rates']
    
    for table in legacy_tables:
        try:
            # Check if table exists and get row count
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = '{table}'
            """))
            
            if result.scalar() > 0:
                # Table exists, check if empty
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                row_count = count_result.scalar()
                
                if row_count > 0:
                    print(f"⚠️  WARNING: {table} has {row_count} rows. Skipping drop for safety.")
                    print(f"   Manual intervention required if data should be migrated.")
                else:
                    # Table is empty, safe to drop
                    op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    print(f"✅ Dropped empty legacy table: {table}")
            else:
                print(f"ℹ️  Table {table} does not exist (already removed or never created)")
                
        except Exception as e:
            print(f"⚠️  Could not check/drop {table}: {e}")
            # Continue with other tables
            pass


def downgrade() -> None:
    """
    Recreate legacy tables (empty) in case rollback is needed.
    
    Note: This only recreates the schema, not the data.
    If data was migrated, manual intervention is required for full rollback.
    """
    # Recreate empty legacy tables with minimal structure
    
    # eq_rates (legacy)
    try:
        op.create_table(
            'eq_rates',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('occupancy_id', sa.Integer(), nullable=True),
            sa.Column('eq_zone', sa.String(length=20), nullable=True),
            sa.Column('eq_rate', sa.Numeric(precision=10, scale=6), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except:
        pass
    
    # stfi_rates (legacy)
    try:
        op.create_table(
            'stfi_rates',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('occupancy_id', sa.Integer(), nullable=True),
            sa.Column('stfi_rate', sa.Numeric(precision=10, scale=6), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except:
        pass
    
    # bsus_rates (legacy)
    try:
        op.create_table(
            'bsus_rates',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('occupancy_id', sa.Integer(), nullable=True),
            sa.Column('eq_zone', sa.String(length=20), nullable=True),
            sa.Column('basic_rate', sa.Numeric(precision=10, scale=6), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except:
        pass
    
    # generic_rates (legacy)
    try:
        op.create_table(
            'generic_rates',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('rate_type', sa.String(length=50), nullable=True),
            sa.Column('rate_value', sa.Numeric(precision=10, scale=6), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except:
        pass
