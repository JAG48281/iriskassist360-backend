"""cleanup_fire_tables_create_iib

Revision ID: ef430ae7e2b6
Revises: 765be293bc72
Create Date: 2025-12-16 15:11:38.929577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef430ae7e2b6'
down_revision: Union[str, None] = '765be293bc72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop Legacy Tables
    tables_to_drop = [
        "product_basic_rates",
        "basic_fire_rates",
        "add_on_rates",
        "addon_rates",
        "pa_rates",
        "product_addon_group_map",
        "add_on_product_map", 
        "addon_groups",
        "stfi_rates", 
        "stfi_rates_old",
        "eq_rates", 
        "eq_rates_common",
        "eq_rates_bsus", 
        "bsus_rates", 
        "eq_zone_rates", 
        "eq_zones",
        "products_master", 
        "product_master"
    ]
    for table in tables_to_drop:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    # 2. Create fire_iib_rates
    op.create_table(
        'fire_iib_rates',
        sa.Column('iib_code', sa.String(length=20), nullable=False),
        sa.Column('rate_per_mille', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('iib_code')
    )

    # 3. Seed Data
    op.execute("INSERT INTO fire_iib_rates (iib_code, rate_per_mille) VALUES ('1001', 0.22), ('1001_2', 0.22), ('2001', 0.35)")


def downgrade() -> None:
    op.drop_table('fire_iib_rates')
