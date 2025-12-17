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
    Calculate risk rate for Fire (UBGR) product.
    Expected request: {"iib_code": "1001", "productCode": "BGRP"}
    Response: {"meta": {"risk_rate": 0.07}}
    """
    try:
        logger.info(f"🧮 Calculate request: productCode={request.productCode}")
        
        # Product Code is already normalized by validator to 'bgrp'
        product_code = request.productCode
        
        if product_code == "bgrp":
            logger.info(f"UBGR normalized to canonical product code: {product_code}")
            # ---------------------------------------------------------
            # UBGR (Bharat Griha Raksha Policy) Strict Rate Lookup
            # ---------------------------------------------------------
            logger.info("UBGR calculate: occupancy validation skipped")
            
            from app.database import engine
            from sqlalchemy import text
            
            # Step 1: Use iib_code directly (No Occupancy Lookup)
            if not request.iib_code:
                # If iib_code missing, check strictness. 
                # User said "iib_code is present" for 200.
                if request.occupancyId:
                     # Fallback to current behavior if user didn't forbid it?
                     # "DO NOT query occupancies table" -> So I cannot use occupancyId to look it up.
                     logger.error("iib_code required for BGRP calculation (Occupancy lookup disabled)")
                     return JSONResponse(
                        status_code=422,
                        content={"error": "iib_code required for BGRP", "success": False}
                     )
                else:
                     logger.error("iib_code missing for BGRP calculation")
                     return JSONResponse(
                        status_code=422,
                        content={"error": "iib_code required", "success": False}
                     )

            iib_code = request.iib_code.strip()
            
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
                
                # TEMPORARY DEBUG LOG as requested
                logger.info(f"UBGR rate resolved: iib_code={iib_code}, rate={risk_rate}")
                
                # RESPONSE CONTRACT (UBGR)
                return {
                    "iib_code": iib_code,
                    "risk_rate_per_mille": risk_rate,
                    "meta": {
                        "risk_rate": risk_rate,
                        "calculation_id": f"calc_{iib_code}_{int(time.time())}",
                        "timestamp": datetime.now().isoformat()
                    },
                    "status": "success",
                    "message": "Risk rate calculated successfully"
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
