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
    total_si: Optional[float] = None  # Added for premium calc

    @validator('productCode')
    def validate_product_code(cls, v):
        # Normalize product_code
        v_clean = v.strip().lower()
        # Resolver
        canonical = PRODUCT_CODE_MAP.get(v_clean.upper(), v_clean)
        
        # If input was BGRP, loop above makes it bgrp (default).
        # We want to support BGRP input too.
        # If canonical is 'bgrp', it's valid.
        
        if canonical not in ["bgrp"]:
             # Legacy support check or strict?
             # Previous: ["BGRP", "UBGR"]
             # Now both map to "bgrp".
             # If user sends "XYZ", it remains "xyz".
             raise ValueError(f"Invalid product code. Must be BGRP/UBGR, got {v}")
        return canonical

@router.post("/calculate")
async def calculate_risk_rate(request: CalculateRequest):
    """
    Calculate risk rate and premium for Fire (UBGR) product.
    Strict implementation for BGRP.
    """
    try:
        logger.info(f"🧮 Calculate request: productCode={request.productCode}")
        
        # Product Code is already normalized by validator to 'bgrp'
        product_code = request.productCode
        
        if product_code == "bgrp":
            logger.info(f"UBGR normalized to canonical product code: {product_code}")
            # ---------------------------------------------------------
            # UBGR (Bharat Griha Raksha Policy) Strict Rate & Premium Calc
            # ---------------------------------------------------------
            logger.info("UBGR calculate: occupancy validation skipped")
            
            from app.database import engine
            from sqlalchemy import text
            from app.utils.rating_engine import round_currency
            from decimal import Decimal
            
            # Step 1: Use iib_code directly (No Occupancy Lookup)
            if not request.iib_code:
                logger.error("iib_code missing for BGRP calculation")
                return JSONResponse(
                   status_code=422,
                   content={"error": "iib_code required", "success": False}
                )

            iib_code = request.iib_code.strip()
            
            # Use total_si from request
            # "Override SI values sent by frontend" -> DO NOT. So we trust request.total_si
            if request.total_si is None:
                # If undefined, we can't calculate premium.
                # User contract says "Response JSON CONTRACT... total_si... basic_fire_premium..."
                # So we must have total_si.
                 logger.error("total_si missing for BGRP calculation")
                 return JSONResponse(
                    status_code=422,
                    content={"error": "total_si required for premium calculation", "success": False}
                 )

            total_si = float(request.total_si)
            
            # Step 2: Query fire_iib_rates ONLY (Strict Match)
            with engine.connect() as conn:
                risk_rate_result = conn.execute(
                    text("SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :iib LIMIT 1"),
                    {"iib": iib_code}
                ).scalar()
                
                if risk_rate_result is None:
                    # FAIL LOUDLY - NO SILENT ZERO
                    logger.error(f"❌ Rate not found for UBGR iib_code='{iib_code}' in fire_iib_rates")
                    return JSONResponse(
                        status_code=404,
                        content={
                            "error": f"Risk rate not found for IIB code {iib_code}", 
                            "success": False,
                            "iib_code": iib_code,
                            "risk_rate_per_mille": None
                        }
                    )
                
                risk_rate = float(risk_rate_result)
                
                # Step 3: Terrorism Rate Lookup
                # "Use terrorism_slabs table. For UBGR -> rate is 0.07 per mille"
                # We use the helper function which queries terrorism_slabs
                try:
                    terrorism_rate_d = get_terrorism_rate_per_mille(
                        product_code="BGRP", # Helper expects BGRP uppercase usually? Or bgrp? 
                        # get_terrorism_rate_per_mille uses input param in query.
                        # Check `get_terrorism_rate_per_mille` source in Step 370.
                        # It uses `WHERE product_code = :p`.
                        # If DB has BGRP, passing "BGRP" is safer.
                        # Wait, product_code variable is 'bgrp' (lowercase) here.
                        # DB likely has 'BGRP'. I should pass "BGRP".
                        occupancy_code=iib_code,
                        tsi=total_si
                    )
                    terrorism_rate = float(terrorism_rate_d)
                except Exception as e:
                    logger.warning(f"Terrorism lookup failed: {e}. Defaulting to 0.07 as per UBGR rule.")
                    terrorism_rate = 0.07 

                # Step 4: Premium Calculation (Strict Logic)
                # basic_fire_premium = total_si × risk_rate_per_mille / 1000
                basic_fire_premium = round_currency(total_si * risk_rate / 1000.0)
                
                # terrorism_premium = terrorism_si × terrorism_rate_per_mille / 1000
                # "Total SI = Terrorism SI"
                terrorism_premium = round_currency(total_si * terrorism_rate / 1000.0)
                
                # Net Premium
                net_premium = basic_fire_premium + terrorism_premium
                
                # taxes
                cgst = round_currency(net_premium * 0.09)
                sgst = round_currency(net_premium * 0.09)
                stamp_duty = 1.0
                
                gross_premium = round_currency(net_premium + cgst + sgst + stamp_duty)
                
                # LOGGING (MANDATORY)
                logger.info("UBGR CALCULATION START")
                logger.info(f"Total SI: {total_si}")
                logger.info(f"Risk Rate (per mille): {risk_rate}")
                logger.info(f"Basic Fire Premium: {basic_fire_premium}")
                logger.info(f"Terrorism Rate (per mille): {terrorism_rate}")
                logger.info(f"Terrorism Premium: {terrorism_premium}")
                logger.info(f"Net Premium: {net_premium}")
                logger.info(f"CGST: {cgst}")
                logger.info(f"SGST: {sgst}")
                logger.info(f"Stamp Duty: {stamp_duty}")
                logger.info(f"Gross Premium: {gross_premium}")

                # RESPONSE CONTRACT (UBGR)
                return {
                    "product_code": "bgrp",
                    "total_si": total_si,
                    "risk_rate_per_mille": risk_rate,
                    "terrorism_rate_per_mille": terrorism_rate,
                    "basic_fire_premium": basic_fire_premium,
                    "terrorism_premium": terrorism_premium,
                    "net_premium": net_premium,
                    "cgst": cgst,
                    "sgst": sgst,
                    "stamp_duty": stamp_duty,
                    "gross_premium": gross_premium
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
