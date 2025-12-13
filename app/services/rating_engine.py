import os
import logging
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy import create_engine, text
from app.schemas.rating_engine import RatingRequest, RatingResponse
from app.utils.rating_engine import round_currency
from app.database import engine

logger = logging.getLogger(__name__)

def get_basic_rate_per_mille(product_code: str, occupancy_code: str, period_years: int = 1) -> Decimal:
    """
    Fetches the basic rate per mille for a given product and occupancy code (iib_code).
    """
    stmt = text("""
        SELECT r.basic_rate 
        FROM product_basic_rates r
        JOIN occupancies o ON r.occupancy_id = o.id
        WHERE r.product_code = :p 
          AND o.iib_code = :o 
        LIMIT 1
    """)
    try:
        with engine.connect() as conn:
            # Note: period_years removed as it's not in the schema currently
            result = conn.execute(stmt, {"p": product_code, "o": occupancy_code}).scalar()
            if result is not None:
                return Decimal(str(result))
            
            logger.warning(f"No basic rate found: Product={product_code}, Occ={occupancy_code}")
            return Decimal("0.0")
    except Exception as e:
        logger.error(f"DB Error (get_basic_rate_per_mille): {e}")
        return Decimal("0.0")

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

    # Query with TSI range check
    stmt = text("""
        SELECT rate_per_mille 
        FROM terrorism_slabs 
        WHERE product_code = :p 
          AND occupancy_type = :ot
          AND si_min <= :tsi
          AND (si_max IS NULL OR si_max >= :tsi)
        ORDER BY rate_per_mille DESC
        LIMIT 1
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, {"p": product_code, "ot": occ_type, "tsi": tsi}).scalar()
            
            if result is not None:
                rate = Decimal(str(result))
                logger.info(f"✅ Selected terrorism rate: {rate} per mille") # Task: Log Selected terrorism rate
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
