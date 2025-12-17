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
            
        # Removed debug code - clean implementation below

        # CRITICAL FIX FOR UBGR RISK RATE AUTO-FILL:
        # occupancyId is the PRIMARY KEY (id) from occupancies table
        # But fire_iib_rates uses iib_code (e.g., "1001") as the key
        # AUTHORITATIVE BUSINESS RULE: UBGR queries ONLY fire_iib_rates
        
        from app.database import engine
        from sqlalchemy import text
        
        try:
            # Step 1: Resolve occupancyId -> iib_code
            with engine.connect() as conn:
                iib_code_result = conn.execute(
                    text("SELECT iib_code FROM occupancies WHERE id = :occ_id"),
                    {"occ_id": request.occupancyId}
                ).scalar()
                
                if not iib_code_result:
                    logger.error(f"❌ Occupancy ID {request.occupancyId} not found")
                    raise ValueError(f"Invalid occupancy ID: {request.occupancyId}")
                
                iib_code = str(iib_code_result)
                logger.info(f"🔍 Resolved: occupancyId={request.occupancyId} -> iib_code={iib_code}")
            
            # Step 2: Query fire_iib_rates with iib_code
            # IGNORE: STFI rates, EQ rates, Add-on rates (as per business rule)
            with engine.connect() as conn:
                risk_rate_result = conn.execute(
                    text("SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :iib"),
                    {"iib": iib_code}
                ).scalar()
                
                if risk_rate_result is not None:
                    risk_rate = float(risk_rate_result)
                    logger.info(
                        f"✅ UBGR Risk Rate: iib_code={iib_code}, rate={risk_rate}‰ "
                        f"(source: fire_iib_rates)"
                    )
                else:
                    logger.error(f"❌ No rate in fire_iib_rates for iib_code={iib_code}")
                    risk_rate = None
                    
        except Exception as e:
            logger.error(f"🔥 Error fetching risk rate: {str(e)}", exc_info=True)
            risk_rate = None

        if risk_rate is None:
            logger.warning(f"⚠️ Risk rate not found for occupancyId={request.occupancyId}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"Risk rate not found for occupancy ID {request.occupancyId}",
                    "meta": {"risk_rate": None}
                }
            )
        
        logger.info(f"✅ Risk rate calculated: {risk_rate}‰")
        
        # RETURN CORRECT FORMAT
        return {
            "meta": {
                "risk_rate": risk_rate,
                "calculation_id": f"calc_{request.occupancyId}_{int(time.time())}",
                "timestamp": datetime.now().isoformat()
            },
            "status": "success",
            "message": "Risk rate calculated successfully"
        }
        
    except Exception as e:
        logger.error(f"🔥 Error in calculate endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal server error: {str(e)}",
                "meta": {"risk_rate": None}
            }
        )
