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
    iib_code = str(occupancy_code)
    
    try:
        with engine.connect() as conn:
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

def get_occupancy_details(occupancy_code: str) -> dict:
    """
    Fetches full occupancy details including all required fields.
    
    Returns dict with keys: id, iib_code, occupancy_type, section_aift, allow_addons
    
    Args:
        occupancy_code: IIB code (e.g., '1001')
        
    Returns:
        dict: Occupancy details or None if not found
    """
    stmt = text("""
        SELECT id, iib_code, occupancy_type, section_aift, allow_addons 
        FROM occupancies 
        WHERE iib_code = :code
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(stmt, {"code": occupancy_code}).fetchone()
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

def get_terrorism_rate_per_mille(product_code: str, occupancy_code: Optional[str] = "1001", tsi: float = 0.0) -> Decimal:
    """
    Fetches the terrorism rate based on TSI slabs.
    Matches product, occupancy type, and TSI range.
    """
    # First get occupancy type for the code
    occ_type = "Residential" # Default
    logger.info(f"Using Occupancy Code: {occupancy_code}") # Task: Log Selected occupancy_code
    
    if occupancy_code:
        # Resolve type
        stmt_type = text("SELECT occupancy_type FROM occupancies WHERE iib_code = :c")
        with engine.connect() as conn:
             res = conn.execute(stmt_type, {"c": occupancy_code}).scalar()
             if res:
                 occ_type = res

    logger.info(f"Looking up Terrorism Rate: Product={product_code}, OccType={occ_type}, TSI={tsi}")

    # Query with TSI range check & Deterministic Ordering
    stmt = text("""
        SELECT rate_per_mille 
        FROM terrorism_slabs 
        WHERE product_code = :p 
          AND occupancy_type = :ot
          AND si_min <= :tsi
          AND (si_max IS NULL OR si_max >= :tsi)
        ORDER BY si_min DESC  -- Deterministic: Pick strict match if multiple ranges overlap (unlikely but safe)
        LIMIT 1
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, {"p": product_code, "ot": occ_type, "tsi": tsi}).scalar()
            
            if result is not None:
                rate = Decimal(str(result))
                logger.info(f"✅ Selected terrorism rate: {rate} per mille") 
                return rate
            
            # Explicit failure if no slab matches
            error_msg = f"No terrorism slab found for Product={product_code}, Type={occ_type}, TSI={tsi}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    except Exception as e:
        logger.error(f"DB Error (get_terrorism_rate_per_mille): {e}")
        raise e

def get_add_on_rate(product_code: str, add_on_code: str, occupancy_code: Optional[str] = None) -> Tuple[str, Decimal]:
    """
    Fetches add-on rate. Handles flexible occupancy rules:
    - rule is NULL or 'ALL' -> Applies to everyone
    - rule is 'ONLY_<code>' -> Applies if occupancy_code == code
    - rule is 'EXCEPT_<code>' -> Applies if occupancy_code != code
    """
    stmt = text("""
        SELECT rate_type, rate_value, occupancy_rule 
        FROM add_on_rates 
        WHERE product_code = :p 
          AND add_on_code = :a 
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"p": product_code, "a": add_on_code}).fetchall()
            
            # Filter logic
            for row in rows:
                rule = row.occupancy_rule
                
                # Match logic
                match = False
                if not rule or rule.upper() == 'ALL':
                    match = True
                elif occupancy_code:
                    if rule.startswith('ONLY_'):
                        target = rule.replace('ONLY_', '')
                        if occupancy_code == target:
                            match = True
                    elif rule.startswith('EXCEPT_'):
                        target = rule.replace('EXCEPT_', '')
                        if occupancy_code != target:
                            match = True
                
                if match:
                    return (row.rate_type, Decimal(str(row.rate_value)))
            
            logger.warning(f"No matching add-on rate found: Product={product_code}, AddOn={add_on_code}, Occ={occupancy_code}")
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
