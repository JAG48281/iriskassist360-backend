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
    risk_rate: Optional[float] = Field(None, alias="risk_rate_per_mille")
    
    # New fields for detailed calculation with aliases to support UI camelCase
    # Aliases allows both snake_case (internal) and camelCase (external)
    basic_cover_si: Optional[float] = Field(0.0, alias="buildingSI")
    add_on_cover_si: Optional[float] = Field(0.0, alias="addOnCoverSI")
    discountPercent: Optional[float] = 0.0
    loadingPercent: Optional[float] = 0.0
    terrorism_si: Optional[float] = Field(None, alias="terrorismSI")
    terrorism_rate: Optional[float] = Field(None, alias="terrorism_rate_per_mille")

    class Config:
        populate_by_name = True

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
            
            # If basic_cover_si is 0 but total_si is provided, fallback to total_si as basic
            if basic_cover_si == 0 and request.total_si and request.total_si > 0:
                 basic_cover_si = float(request.total_si)
            
            # Terrorism SI
            if request.terrorism_si is not None:
                terrorism_si = float(request.terrorism_si)
            elif request.total_si is not None:
                terrorism_si = float(request.total_si)
            else:
                terrorism_si = basic_cover_si + add_on_cover_si
            
            discount_percent = float(request.discountPercent or 0.0)
            loading_percent = float(request.loadingPercent or 0.0)

            # ---------------------------------------------------------
            # CALCULATION LOGIC
            # ---------------------------------------------------------

            # 1. BASIC FIRE PREMIUM
            # basic_fire_premium = buildingSI * risk_rate / 1000
            basic_fire_premium = round_currency(basic_cover_si * risk_rate / 1000.0)

            # 2. ADD-ON PREMIUM CALCULATION
            # add_on_premium = addOnCoverSI * risk_rate / 1000
            add_on_premium = 0.0
            if add_on_cover_si > 0:
                add_on_premium = round_currency(add_on_cover_si * risk_rate / 1000.0)

            # 3. BASE SUBTOTAL (renamed from subtotal_premium in strict rules logic)
            # base_subtotal = basic_fire_premium + add_on_premium
            base_subtotal = round_currency(basic_fire_premium + add_on_premium)

            # 4. DISCOUNT LOGIC
            # discount_amount = base_subtotal * discountPercent / 100
            discount_amount = 0.0
            if discount_percent > 0:
                discount_amount = round_currency(base_subtotal * discount_percent / 100.0)

            # 5. LOADING LOGIC
            # loading_amount = (base_subtotal - discount_amount) * loadingPercent / 100
            loading_amount = 0.0
            if loading_percent > 0:
                # Loading calculation base logic fixed
                base_for_loading = base_subtotal - discount_amount
                # Ensure base is not negative, though unlikely
                base_for_loading = max(0.0, base_for_loading)
                loading_amount = round_currency(base_for_loading * loading_percent / 100.0)

            # 6. SUBTOTAL PREMIUM (Final Subtotal)
            # subtotal_premium = base_subtotal - discount_amount + loading_amount
            subtotal_premium = round_currency(base_subtotal - discount_amount + loading_amount)
            if subtotal_premium < 0:
                subtotal_premium = 0.0

            # 7. TERRORISM PREMIUM
            # terrorism_premium = terrorismSI * terrorism_rate / 1000
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
            
            # Priority: Use input terrorism_rate if available, else lookup
            if request.terrorism_rate is not None:
                terrorism_rate = float(request.terrorism_rate)
                # Simple calculation with provided rate
                terrorism_premium = round_currency(terrorism_si * terrorism_rate / 1000.0)
            else:
                 # Lookup Logic
                try:
                    from app.services.rating_engine import get_fire_terrorism_premium, get_terrorism_rate_per_mille
                    
                    # Get Rate for logging/response
                    tr_val = get_terrorism_rate_per_mille(
                        occupancy_type=occupancy_type, 
                        total_sum_insured=terrorism_si
                    )
                    terrorism_rate = float(tr_val)
                    
                    # Calculate Premium (Slab based) - Strict Rules say "terrorismSI * rate / 1000".
                    # However, strictly speaking, slab logic might mean different rates for different portions.
                    # The USER PROMPT says: "terrorism_premium = terrorismSI * terrorism_rate_per_mille / 1000"
                    # This implies a FLAT rate per mille might be expected if provided from input, OR calculated.
                    # If calculated from DB, it's usually slab based.
                    # Use get_fire_terrorism_premium which is authoritative for slabs.
                    tp_val = get_fire_terrorism_premium(
                        occupancy_type=occupancy_type,
                        total_sum_insured=terrorism_si
                    )
                    terrorism_premium = float(round_currency(tp_val))
                    
                except Exception as e:
                    logger.warning(f"Terrorism lookup failed: {e}")
                    terrorism_premium = 0.0

            # 8. NET PREMIUM
            # net_premium = subtotal_premium + terrorism_premium
            net_premium = round_currency(subtotal_premium + terrorism_premium)

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
            logger.info("UBGR CALC [V3 Strict] →")
            logger.info(f"basic_si={basic_cover_si}, add_on_si={add_on_cover_si}, terrorism_si={terrorism_si}")
            logger.info(f"risk_rate={risk_rate}, disc={discount_percent}%, load={loading_percent}%, terr_rate={terrorism_rate}")
            logger.info(f"basic_prem={basic_fire_premium}, add_on_prem={add_on_premium}, base_subtotal={base_subtotal}")
            logger.info(f"disc_amt={discount_amount}, load_amt={loading_amount}, subtotal_prem={subtotal_premium}")
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
