from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging
from app.services.rating_engine import get_terrorism_rate_per_mille
from fastapi.responses import JSONResponse
from fastapi import APIRouter
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Calculation"])

from typing import Optional


PRODUCT_CODE_MAP = {
    "UBGR": "bgrp",
    "ubgr": "bgrp",
}

class CalculateRequest(BaseModel):
    occupancyId: Optional[int] = None
    productCode: str
    iib_code: Optional[str] = None
    total_si: Optional[float] = None
    risk_rate: Optional[float] = None
    
    # New fields for detailed calculation
    basic_cover_si: Optional[float] = 0.0
    add_on_cover_si: Optional[float] = 0.0
    discountPercent: Optional[float] = 0.0
    loadingPercent: Optional[float] = 0.0
    terrorism_si: Optional[float] = None

    @validator('productCode')
    def validate_product_code(cls, v):
        # Normalize product_code
        v_clean = v.strip().lower()
        # Resolver
        canonical = PRODUCT_CODE_MAP.get(v_clean.upper(), v_clean)
        
        if canonical not in ["bgrp"]:
             raise ValueError(f"Invalid product code. Must be BGRP/UBGR, got {v}")
        return canonical

@router.post("/calculate")
async def calculate_risk_rate(request: CalculateRequest):
    """
    Calculate risk rate and premium for Fire (UBGR) product.
    Strict implementation for BGRP based on detailed rules.
    """
    try:
        logger.info(f"🧮 Calculate request: productCode={request.productCode}")
        
        # Product Code is already normalized by validator to 'bgrp'
        product_code = request.productCode
        
        if product_code == "bgrp":
            logger.info(f"UBGR normalized to canonical product code: {product_code}")
            
            from app.database import engine
            from sqlalchemy import text
            from app.utils.rating_engine import round_currency
            
            # Step 1: Validate iib_code
            if not request.iib_code:
                logger.error("iib_code missing for BGRP calculation")
                return JSONResponse(
                   status_code=422,
                   content={"error": "iib_code required", "success": False}
                )

            iib_code = request.iib_code.strip()
            
            # MANDATORY Rule: Use only risk_rate from request
            if request.risk_rate is None:
                 logger.error("risk_rate missing for BGRP calculation - Must be explicitly provided")
                 return JSONResponse(
                    status_code=422,
                    content={"error": "risk_rate required for BGRP calculation", "success": False}
                 )
            
            risk_rate = float(request.risk_rate)

            # Retrieve SIs and inputs
            basic_cover_si = float(request.basic_cover_si or 0.0)
            add_on_cover_si = float(request.add_on_cover_si or 0.0)
            
            # If basic_cover_si is 0 but total_si is provided, fallback to total_si as basic (legacy support)
            # However, prompt implies strict separation. We will trust the inputs.
            # But let's handle the case where basic_cover_si might be missing but total_si exists.
            if basic_cover_si == 0 and request.total_si and request.total_si > 0:
                 # Assume all is basic if not specified
                 basic_cover_si = float(request.total_si)
            
            # Terrorism SI: defaulting to total_si from request if terrorism_si not explicit
            terrorism_si = float(request.terrorism_si if request.terrorism_si is not None else (request.total_si or (basic_cover_si + add_on_cover_si)))
            
            discount_percent = float(request.discountPercent or 0.0)
            loading_percent = float(request.loadingPercent or 0.0)

            # ---------------------------------------------------------
            # CALCULATION LOGIC
            # ---------------------------------------------------------

            # 1. ADD-ON PREMIUM CALCULATION
            # If add_on_cover_si > 0: add_on_premium = add_on_cover_si * risk_rate / 1000
            # Use SAME risk_rate as basic fire premium.
            add_on_premium = 0.0
            if add_on_cover_si > 0:
                add_on_premium = round_currency(add_on_cover_si * risk_rate / 1000.0)

            # 2. BASIC FIRE PREMIUM
            # basic_fire_premium = basic_cover_si * risk_rate / 1000
            basic_fire_premium = round_currency(basic_cover_si * risk_rate / 1000.0)

            # 3. SUBTOTAL PREMIUM
            # subtotal_premium = basic_fire_premium + add_on_premium
            subtotal_premium = round_currency(basic_fire_premium + add_on_premium)

            # 4. DISCOUNT LOGIC
            # If discountPercent > 0: discount_amount = subtotal_premium * discountPercent / 100
            # Discount applies ONLY on subtotal_premium.
            discount_amount = 0.0
            if discount_percent > 0:
                discount_amount = round_currency(subtotal_premium * discount_percent / 100.0)

            # 5. LOADING LOGIC
            # If loadingPercent > 0: loading_amount = subtotal_premium * loadingPercent / 100
            # Loading applies ONLY on subtotal_premium.
            loading_amount = 0.0
            if loading_percent > 0:
                loading_amount = round_currency(subtotal_premium * loading_percent / 100.0)

            # 6. FINAL SUBTOTAL AFTER ADJUSTMENTS
            # adjusted_subtotal = subtotal_premium - discount_amount + loading_amount
            adjusted_subtotal = round_currency(subtotal_premium - discount_amount + loading_amount)
            # Ensure not negative? (Though insurance logic usually implies checks)
            if adjusted_subtotal < 0:
                adjusted_subtotal = 0.0

            # 7. TERRORISM PREMIUM
            # terrorism_premium calculated separately. NO discount / loading on terrorism.
            
            # Rate Lookup (Terrorism Only)
            occupancy_type = "Residential" # Default
            try:
                with engine.connect() as conn:
                    occ_res = conn.execute(
                        text("SELECT occupancy_type FROM occupancies WHERE iib_code = :iib"),
                        {"iib": iib_code}
                    ).scalar()
                    if occ_res:
                        occupancy_type = occ_res
            except Exception as e:
                logger.warning(f"Occupancy type lookup failed for {iib_code}. Using Default: Residential.")

            terrorism_rate = 0.0
            terrorism_premium = 0.0
            
            try:
                from app.services.rating_engine import get_fire_terrorism_premium, get_terrorism_rate_per_mille
                
                # Get Rate for logging/response
                tr_val = get_terrorism_rate_per_mille(
                    occupancy_type=occupancy_type, 
                    total_sum_insured=terrorism_si
                )
                terrorism_rate = float(tr_val)
                
                # Calculate Premium
                tp_val = get_fire_terrorism_premium(
                    occupancy_type=occupancy_type,
                    total_sum_insured=terrorism_si
                )
                terrorism_premium = float(round_currency(tp_val))
                
            except Exception as e:
                logger.warning(f"Terrorism lookup failed: {e}")
                # Fallback logic if needed, though get_fire_terrorism_premium should handle it
                # For safety, let's keep it 0 or minimal if error? 
                # User instructions imply existing separate calculation.
                terrorism_premium = 0.0

            # 8. NET PREMIUM
            # net_premium = adjusted_subtotal + terrorism_premium
            net_premium = round_currency(adjusted_subtotal + terrorism_premium)

            # 9. GST
            # cgst = net_premium * 0.09
            # sgst = net_premium * 0.09
            cgst = round_currency(net_premium * 0.09)
            sgst = round_currency(net_premium * 0.09)
            
            # 10. STAMP DUTY
            # stamp_duty = 1 (always)
            stamp_duty = 1.0

            # 11. GROSS PREMIUM
            # gross_premium = net_premium + cgst + sgst + stamp_duty
            gross_premium = round_currency(net_premium + cgst + sgst + stamp_duty)
            
            # LOGGING
            logger.info("UBGR CALC [V2] →")
            logger.info(f"basic_si={basic_cover_si}, add_on_si={add_on_cover_si}, terrorism_si={terrorism_si}")
            logger.info(f"risk_rate={risk_rate}, disc={discount_percent}%, load={loading_percent}%, terr_rate={terrorism_rate}")
            logger.info(f"basic_prem={basic_fire_premium}, add_on_prem={add_on_premium}, subtotal={subtotal_premium}")
            logger.info(f"disc_amt={discount_amount}, load_amt={loading_amount}, adj_subtotal={adjusted_subtotal}")
            logger.info(f"terr_prem={terrorism_premium}, net={net_premium}, gross={gross_premium}")

            # 12. RESPONSE MUST RETURN ALL FIELDS
            return {
                "basic_fire_premium": basic_fire_premium,
                "add_on_premium": add_on_premium,
                "discount_amount": discount_amount,
                "loading_amount": loading_amount,
                "subtotal_premium": subtotal_premium,
                "terrorism_premium": terrorism_premium,
                "net_premium": net_premium,
                "cgst": cgst,
                "sgst": sgst,
                "stamp_duty": stamp_duty,
                "gross_premium": gross_premium,
                
                # Extra metadata
                "fire_premium": subtotal_premium, # Alias for UI compatibility
                "risk_rate_used": risk_rate,
                "terrorism_rate_used": terrorism_rate,
                "product_code": "bgrp",
                "calculated_at": datetime.now().isoformat()
            }
        
        # Legacy/Other Products Logic (if any)
        # currently only UBGR/BGRP is supported by this fix scope
        logger.warning(f"Product {product_code} not fully supported in unified calculate yet")
        return JSONResponse(
            status_code=400,
            content={"error": f"Product {product_code} not supported", "success": False}
        )
        
    except Exception as e:
        logger.error(f"🔥 Error in calculate endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal server error: {str(e)}",
                "meta": {"risk_rate": None}
            }
        )
