import os
import logging
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy import create_engine, text
from app.schemas.rating_engine import RatingRequest, RatingResponse
from app.utils.rating_engine import round_currency

logger = logging.getLogger(__name__)

# Database Connection
# Ensure DATABASE_URL is set in environment or .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.warning("DATABASE_URL not set, rating engine DB functions may fail.")
    # Fallback/Placeholder
    DATABASE_URL = "postgresql://postgres:user@localhost/dbname"

engine = create_engine(DATABASE_URL)

def get_basic_rate_per_mille(product_code: str, occupancy_code: str, period_years: int = 1) -> Decimal:
    """
    Fetches the basic rate per mille for a given product and occupancy.
    """
    stmt = text("""
        SELECT rate_per_mille 
        FROM product_basic_rates 
        WHERE product_code = :p 
          AND occupancy_code = :o 
          AND period_years = :y 
        LIMIT 1
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, {"p": product_code, "o": occupancy_code, "y": period_years}).scalar()
            if result is not None:
                return Decimal(str(result))
            
            logger.warning(f"No basic rate found: Product={product_code}, Occ={occupancy_code}, Years={period_years}")
            return Decimal("0.0")
    except Exception as e:
        logger.error(f"DB Error (get_basic_rate_per_mille): {e}")
        return Decimal("0.0")

def get_terrorism_rate_per_mille(product_code: str) -> Decimal:
    """
    Fetches the terrorism rate. Falls back to a default if not found.
    """
    stmt = text("""
        SELECT rate_per_mille 
        FROM terrorism_slabs 
        WHERE product_code = :p 
        ORDER BY effective_date DESC 
        LIMIT 1
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, {"p": product_code}).scalar()
            if result is not None:
                return Decimal(str(result))
            
            # Fallback for known products if table is empty
            logger.warning(f"No terrorism rate found for Product={product_code}. Returning 0.0.")
            return Decimal("0.0")
    except Exception as e:
        logger.error(f"DB Error (get_terrorism_rate_per_mille): {e}")
        return Decimal("0.0")

def get_add_on_rate(product_code: str, add_on_code: str, occupancy_rule: Optional[str] = None) -> Tuple[str, Decimal]:
    """
    Fetches add-on rate type and value.
    Returns (rate_type, rate_value). rate_value is Decimal.
    """
    stmt = text("""
        SELECT rate_type, rate_value 
        FROM add_on_rates 
        WHERE product_code = :p 
          AND add_on_code = :a 
          AND (occupancy_rule IS NULL OR occupancy_rule = :rule)
        LIMIT 1
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(stmt, {"p": product_code, "a": add_on_code, "rule": occupancy_rule}).first()
            if row:
                return (row[0], Decimal(str(row[1])))
            
            logger.warning(f"No add-on rate found: Product={product_code}, AddOn={add_on_code}, Rule={occupancy_rule}")
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
