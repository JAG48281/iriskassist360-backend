import os
import logging
from decimal import Decimal
from typing import Optional, Tuple, Union
from sqlalchemy import create_engine, text
from app.schemas.rating_engine import RatingRequest, RatingResponse
from app.utils.rating_engine import round_currency
from app.database import engine

logger = logging.getLogger(__name__)


def get_basic_rate_per_mille(product_code: str, occupancy_code: Union[str, int], eq_zone: Optional[str] = None, period_years: int = 1) -> Decimal:
    """
    Fetches the basic rate per mille for a given product and occupancy code (iib_code).
    
    Refactored to use clean rate architecture:
    1. BSUS -> fire_bsus_rates (Key: iib_code + eq_zone)
    2. Others -> fire_iib_rates (Key: iib_code)
    
    Args:
        product_code: Product code (e.g., 'UBGR', 'BGRP', 'BSUS')
        occupancy_code: IIB code (e.g., '1001')
        eq_zone: Earthquake Zone (Required for BSUS)
        period_years: Policy period (not currently used in schema)
    
    Returns:
        Decimal: Basic rate per mille
        
    Raises:
        ValueError: If no rate is configured or inputs invalid
    """
    val = str(occupancy_code)
    iib_code = val
    
    try:
        with engine.connect() as conn:
            # If occupancy_code looks like a DB ID, resolve it to iib_code first
            if val.isdigit() and len(val) < 8: # Small int likely an ID
                 res = conn.execute(text("SELECT iib_code FROM occupancies WHERE id = :id"), {"id": int(val)}).scalar()
                 if res:
                     iib_code = res
                     
            if product_code.upper() == "BSUS":
                if not eq_zone:
                    raise ValueError("EQ Zone is required for BSUS rating")
                    
                # BSUS LOOKUP
                stmt = text("""
                    SELECT rate_per_mille 
                    FROM fire_bsus_rates 
                    WHERE iib_code = :iib 
                      AND eq_zone = :zone
                """)
                row = conn.execute(stmt, {"iib": iib_code, "zone": eq_zone}).fetchone()
                src_table = "fire_bsus_rates"
                
            else:
                # STANDARD LOOKUP (UBGR, BGRP, etc.)
                stmt = text("""
                    SELECT rate_per_mille 
                    FROM fire_iib_rates 
                    WHERE iib_code = :iib
                """)
                row = conn.execute(stmt, {"iib": iib_code}).fetchone()
                src_table = "fire_iib_rates"

            if row:
                rate = Decimal(str(row.rate_per_mille))
                logger.info(
                    f"🔥 Fire Rate Applied | Product={product_code} "
                    f"IIB={iib_code} EQ={eq_zone} Rate={rate}‰ (Table: {src_table})"
                )
                return rate
            
            # Not Found Error
            error_msg = f"Rate not found in {src_table} for IIB={iib_code}"
            if product_code.upper() == "BSUS":
                error_msg += f", EQ={eq_zone}"
            
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"DB Error (get_basic_rate_per_mille): {e}")
        raise ValueError(f"Database error while fetching basic rate: {str(e)}")

def get_fire_eq_rate_per_mille(iib_code: str, eq_zone: str) -> Decimal:
    """
    Fetches Earthquake (EQ) rate from fire_eq_rates.
    Key: iib_code + eq_zone
    """
    stmt = text("""
        SELECT eq_rate 
        FROM fire_eq_rates 
        WHERE iib_code = :iib 
          AND eq_zone = :zone
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(stmt, {"iib": iib_code, "zone": eq_zone}).fetchone()
            if row:
                rate = Decimal(str(row.eq_rate))
                logger.info(f"✅ EQ Rate Lookup: IIB={iib_code} Zone={eq_zone} -> {rate}‰")
                return rate
            
            error_msg = f"EQ Rate not found for IIB={iib_code} Zone={eq_zone}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"DB Error (get_fire_eq_rate_per_mille): {e}")
        raise ValueError(f"EQ Rate Fetch Error: {str(e)}")

def get_stfi_rate_per_mille(iib_code: str) -> Decimal:
    """
    Fetches STFI rate from fire_iib_rates (as proxy/default).
    Key: iib_code
    """
    stmt = text("""
        SELECT rate_per_mille 
        FROM fire_iib_rates 
        WHERE iib_code = :iib
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(stmt, {"iib": iib_code}).fetchone()
            if row:
                rate = Decimal(str(row.rate_per_mille))
                logger.info(f"✅ STFI Rate Lookup (from IIB): IIB={iib_code} -> {rate}‰")
                return rate
            
            error_msg = f"STFI Rate not found for IIB={iib_code}"
            logger.error(f"❌ {error_msg}")
            return Decimal("0.0") 
    except Exception as e:
        logger.error(f"DB Error (get_stfi_rate_per_mille): {e}")
        return Decimal("0.0")

def get_occupancy_details(occupancy_code: Union[str, int]) -> dict:
    """
    Fetches full occupancy details. Handles both DB ID or IIB Code.
    """
    # Determine if occupancy_code is an ID (integer/numeric string) or IIB code
    try:
        # If it can be cast to int, try matching by ID first, then by iib_code
        occ_id = int(str(occupancy_code))
        stmt = text("""
            SELECT id, iib_code, occupancy_type, section_aift, allow_addons 
            FROM occupancies 
            WHERE id = :val OR iib_code = CAST(:val AS VARCHAR)
        """)
        val = occ_id
    except (ValueError, TypeError):
        # Otherwise match by iib_code
        stmt = text("""
            SELECT id, iib_code, occupancy_type, section_aift, allow_addons 
            FROM occupancies 
            WHERE iib_code = :val
        """)
        val = str(occupancy_code)

    try:
        with engine.connect() as conn:
            row = conn.execute(stmt, {"val": val}).fetchone()
            if row:
                details = {
                    "id": row.id,
                    "iib_code": row.iib_code,
                    "occupancy_type": row.occupancy_type,
                    "section_aift": row.section_aift,
                    "allow_addons": row.allow_addons
                }
                logger.info(f"📋 Occupancy Details: {occupancy_code} → ID={row.id}, Type={row.occupancy_type}, Section={row.section_aift}")
                return details
            
            logger.warning(f"⚠️ Occupancy not found: {occupancy_code}")
            return None
    except Exception as e:
        logger.error(f"DB Error (get_occupancy_details): {e}")
        return None

def get_terrorism_rate_per_mille(occupancy_type: str, total_sum_insured: float) -> Decimal:
    """
    Get terrorism rate based on Occupancy Type and Total SI.
    Strictly Product-Agnostic.
    """
    stmt = text("""
        SELECT rate_per_mille
        FROM fire_terrorism_rates
        WHERE occupancy_type = :ot
          AND :tsi >= min_sum_insured
          AND (:tsi < max_sum_insured OR max_sum_insured IS NULL)
        ORDER BY min_sum_insured DESC
        LIMIT 1;
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, {"ot": occupancy_type, "tsi": total_sum_insured}).scalar()
            
            if result is not None:
                rate = Decimal(str(result))
                logger.info(f"Terrorism Rate Lookup → OccType={occupancy_type}, TSI={total_sum_insured}, Rate={rate}")
                return rate
            
            # Explicit error if not found
            msg = f"No terrorism rate found for OccType={occupancy_type}, TSI={total_sum_insured}"
            logger.error(msg)
            raise ValueError(msg)
            
    except Exception as e:
        logger.error(f"DB Error (get_terrorism_rate_per_mille): {e}")
        raise e

def get_terrorism_slabs(occupancy_type: str) -> list:
    """
    Fetches all terrorism slabs for a given occupancy type.
    Ordered by min_sum_insured ASC.
    """
    stmt = text("""
        SELECT min_sum_insured, max_sum_insured, rate_per_mille
        FROM fire_terrorism_rates
        WHERE occupancy_type = :ot
        ORDER BY min_sum_insured ASC
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, {"ot": occupancy_type}).fetchall()
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"DB Error (get_terrorism_slabs): {e}")
        return []

def get_fire_terrorism_premium(occupancy_type: str, total_sum_insured: float) -> float:
    """
    Calculates total terrorism premium based on progressive slabs.
    Progressive means: first slab applies to first range, second to next range, etc.
    """
    slabs = get_terrorism_slabs(occupancy_type)
    if not slabs:
        logger.warning(f"No terrorism slabs found for occupancy_type={occupancy_type}")
        return 0.0
    
    total_premium = Decimal("0")
    remaining_si = Decimal(str(total_sum_insured))

    for slab in slabs:
        min_si = Decimal(str(slab['min_sum_insured']))
        max_si = slab['max_sum_insured']
        rate = Decimal(str(slab['rate_per_mille']))

        # Calculate slab width
        upper = Decimal(str(max_si)) if max_si is not None else remaining_si + min_si
        slab_width = upper - min_si

        # Apply to this slab
        applied_si = min(remaining_si, slab_width)
        if applied_si <= 0:
            break

        premium_for_slab = (applied_si * rate) / Decimal("1000")
        total_premium += premium_for_slab
        remaining_si -= applied_si

        if remaining_si <= 0:
            break
            
    return float(total_premium)

def calculate_terrorism_premium(occupancy_type: str, total_sum_insured: float) -> float:
    """Legacy wrapper for get_fire_terrorism_premium"""
    return get_fire_terrorism_premium(occupancy_type, total_sum_insured)

def get_add_on_rate(product_code: str, add_on_code: str, occupancy_code: Optional[str] = None) -> Tuple[str, Decimal]:
    """
    Fetches add-on rate from fire_add_on_rates.
    Matches product_code against pipe-separated product_group.
    Returns (pricing_type, rate_value).
    """
    stmt = text("""
        SELECT pricing_type, rate_value, product_group 
        FROM fire_add_on_rates 
        WHERE add_on_code = :a 
          AND is_active = true
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"a": add_on_code}).fetchall()
            
            for row in rows:
                pgroups = [p.strip().upper() for p in row.product_group.split("|")]
                if product_code.upper() in pgroups:
                    return (row.pricing_type, Decimal(str(row.rate_value)))
            
            # If not found specifically for product, implies no rate/not applicable
            logger.info(f"AddOn {add_on_code} not configured for {product_code} in fire_add_on_rates.")
            return ("fixed", Decimal("0.0"))
            
    except Exception as e:
        logger.error(f"DB Error (get_add_on_rate): {e}")
        return ("fixed", Decimal("0.0"))

class RatingService:
    @staticmethod
    def calculate_premium(request: RatingRequest) -> RatingResponse:
        """
        Calculates premium based on the provided rate in request.
        To use DB lookup, the caller should retrieve the rate using helper functions first 
        and pass it in request.rate, OR we augment this service to look it up if 
        request implies a lookup (not implemented in this step to preserve existing API contract).
        """
        
        base_premium = round_currency(request.sum_insured * request.rate / 1000)
        
        current_premium = base_premium
        breakdown = {"base": base_premium}
        
        # Apply loadings
        total_loading = sum(request.loadings_pct)
        loading_amount = round_currency(base_premium * total_loading / 100)
        current_premium += loading_amount
        breakdown["loadings"] = loading_amount
        
        # Apply discounts
        total_discount = sum(request.discounts_pct)
        discount_amount = round_currency(current_premium * total_discount / 100)
        current_premium -= discount_amount
        breakdown["discounts"] = discount_amount
        
        net_premium = max(0, current_premium)
        
        # GST (18%)
        gst_rate = 0.18
        total_gst = round_currency(net_premium * gst_rate)
        cgst = round_currency(total_gst / 2)
        sgst = round_currency(total_gst / 2)
        
        final_premium = round_currency(net_premium + total_gst)
        
        return RatingResponse(
            base_premium=base_premium,
            net_premium=net_premium,
            cgst=cgst,
            sgst=sgst,
            igst=0.0,
            total_premium=final_premium,
            breakdown=breakdown
        )
