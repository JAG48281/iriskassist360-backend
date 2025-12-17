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
    risk_rate: Optional[float] = None # Added per mandatory rules

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
            
            # Step 1: Validate iib_code (for completeness) and explicit inputs
            if not request.iib_code:
                logger.error("iib_code missing for BGRP calculation")
                return JSONResponse(
                   status_code=422,
                   content={"error": "iib_code required", "success": False}
                )

            iib_code = request.iib_code.strip()
            
            # MANDATORY Rule 1: Use only risk_rate from request
            if request.risk_rate is None:
                 logger.error("risk_rate missing for BGRP calculation - Must be explicitly provided")
                 return JSONResponse(
                    status_code=422,
                    content={"error": "risk_rate required for BGRP calculation", "success": False}
                 )
            
            risk_rate = float(request.risk_rate)

            # MANDATORY Rule 2: Total SI presence
            if request.total_si is None:
                 logger.error("total_si missing for BGRP calculation")
                 return JSONResponse(
                    status_code=422,
                    content={"error": "total_si required for premium calculation", "success": False}
                 )

            total_si = float(request.total_si)
            
            # Step 2: Rate Lookup (Terrorism Only) - BGRP Specific
            try:
                terrorism_rate_d = get_terrorism_rate_per_mille(
                    product_code="BGRP", 
                    occupancy_code=iib_code,
                    tsi=total_si
                )
                terrorism_rate = float(terrorism_rate_d)
            except Exception as e:
                logger.warning(f"Terrorism lookup failed: {e}. Defaulting to 0.07 as per BGRP standard.")
                terrorism_rate = 0.07 

            # Step 3: Premium Calculation (Strict Logic)
            # fire_premium = total_si * risk_rate / 1000
            fire_premium = round_currency(total_si * risk_rate / 1000.0)
            
            # terrorism_premium = terrorism_si * terrorism_rate / 1000
            # (Rule: Total SI = Terrorism SI)
            terrorism_premium = round_currency(total_si * terrorism_rate / 1000.0)
            
            # Net Premium
            net_premium = fire_premium + terrorism_premium
            
            # GST (18%)
            gst = round_currency(net_premium * 0.18)
            
            # Stamp Duty (Flat 1)
            stamp_duty = 1.0
            
            # Gross
            gross_premium = round_currency(net_premium + gst + stamp_duty)
            
            # LOGGING (MANDATORY STRICT FORMAT)
            logger.info("UBGR CALC →")
            logger.info(f"total_si={total_si}")
            logger.info(f"risk_rate={risk_rate}")
            logger.info(f"terrorism_rate={terrorism_rate}")
            logger.info(f"fire={fire_premium}")
            logger.info(f"terrorism={terrorism_premium}")
            logger.info(f"net={net_premium}")

            # RESPONSE CONTRACT (STRICT)
            return {
                "fire_premium": fire_premium,
                "terrorism_premium": terrorism_premium,
                "net_premium": net_premium,
                "gst": gst,
                "gross_premium": gross_premium,
                "risk_rate_used": risk_rate,
                "terrorism_rate_used": terrorism_rate,
                # Extra fields for frontend context if needed, but contract specified explicitly these
                "product_code": "bgrp",
                "total_si": total_si,
                "stamp_duty": stamp_duty # Implicitly needed for gross check
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
