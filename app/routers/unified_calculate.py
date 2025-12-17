from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging
from app.services.rating_engine import get_terrorism_rate_per_mille
from fastapi.responses import JSONResponse
from fastapi import APIRouter
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Calculation"])

class CalculateRequest(BaseModel):
    occupancyId: int
    productCode: str
    
    @validator('productCode')
    def validate_product_code(cls, v):
        v = v.upper().strip()
        if v not in ["BGRP", "UBGR"]:  # Accept both formats
            raise ValueError(f"Invalid product code. Must be BGRP/UBGR, got {v}")
        return v

@router.post("/calculate")
async def calculate_risk_rate(request: CalculateRequest):
    """
    Calculate risk rate for Fire (UBGR) product.
    Expected request: {"occupancyId": 1001, "productCode": "BGRP"}
    Response: {"meta": {"risk_rate": 0.07}}
    """
    try:
        logger.info(f"🧮 Calculate request: occupancyId={request.occupancyId}, productCode={request.productCode}")
        print(f"DEBUG: Processing occupancyId={request.occupancyId} productCode={request.productCode}", flush=True)
        
        # Normalize Product Code
        product_code = request.productCode
        if product_code == "UBGR":
            product_code = "BGRP"
            
        if product_code == "BGRP":
            # ---------------------------------------------------------
            # UBGR (Bharat Griha Raksha Policy) Strict Rate Lookup
            # ---------------------------------------------------------
            from app.database import engine
            from sqlalchemy import text
            
            # Step 1: Resolve occupancyId -> iib_code (Strict String)
            with engine.connect() as conn:
                iib_code_result = conn.execute(
                    text("SELECT iib_code FROM occupancies WHERE id = :occ_id"),
                    {"occ_id": request.occupancyId}
                ).scalar()
                
                if not iib_code_result:
                    logger.error(f"❌ Occupancy ID {request.occupancyId} not found")
                    return JSONResponse(
                        status_code=404,
                        content={"error": f"Occupancy ID {request.occupancyId} not found", "success": False}
                    )
                
                # STRICT: Trim whitespace only, NO casting to int
                iib_code = str(iib_code_result).strip()
            
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
                        "calculation_id": f"calc_{request.occupancyId}_{int(time.time())}",
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
