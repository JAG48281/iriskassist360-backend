"""
Fire Insurance Premium Calculation Router
Implements authoritative premium calculation endpoints for UBGR/UVGR/UVGS products.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.fire_premium import UBGRUVGRRequest, UBGRUVGRResponse
from app.services.fire_premium_service import FirePremiumCalculator
from app.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fire",
    tags=["Fire Insurance Premium"],
    responses={404: {"description": "Not found"}},
)

@router.post("/ubgr/calculate", response_model=UBGRUVGRResponse)
@limiter.limit("30/minute")
def calculate_ubgr_premium(
    request: Request,
    payload: UBGRUVGRRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate premium for UBGR (United Bharat Griha Raksha) product.
    
    **Calculation Flow:**
    1. Basic Fire Premium = Total SI × Basic Rate / 1000
    2. Add-On Premium = Sum of all add-on premiums + PA premiums
    3. Discount Amount = (Basic Fire + Add-On) × Discount %
    4. Subtotal = (Basic Fire + Add-On) - Discount
    5. Loading Amount = Subtotal × Loading %
    6. Terrorism Premium = Total SI × Terrorism Rate / 1000 (excluded from discount/loading)
    7. Net Premium = Subtotal + Loading + Terrorism
    8. Gross Premium = Net + CGST + SGST + Stamp Duty
    
    **Business Rules:**
    - Discount applies ONLY on (Basic Fire + Add-On)
    - Loading applies ONLY on Subtotal
    - Terrorism is added AFTER Loading
    - All rates fetched from database
    """
    try:
        logger.info(f"UBGR Premium Calculation Request: {payload.model_dump()}")
        
        # Override product code to ensure UBGR
        payload.productCode = "UBGR"

        # Defensive Validation: UBGR requires explicit risk rate
        if payload.risk_rate_per_mille is None:
            logger.error("Validation Failed: Risk rate missing for UBGR calculation")
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Risk rate missing for UBGR calculation"
                }
            )
        
        result = FirePremiumCalculator.calculate_ubgr_uvgr(payload)
        return UBGRUVGRResponse(**result)
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calculation Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Premium calculation failed: {str(e)}")

@router.post("/uvgr/calculate", response_model=UBGRUVGRResponse)
@limiter.limit("30/minute")
def calculate_uvgr_premium(
    request: Request,
    payload: UBGRUVGRRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate premium for UVGR (United Value Griha Raksha) product.
    
    Uses identical calculation logic as UBGR.
    See /ubgr/calculate for detailed calculation flow.
    """
    try:
        logger.info(f"UVGR Premium Calculation Request: {payload.model_dump()}")
        
        # Override product code to ensure UVGR
        payload.productCode = "UVGR"
        
        result = FirePremiumCalculator.calculate_ubgr_uvgr(payload)
        return UBGRUVGRResponse(**result)
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calculation Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Premium calculation failed: {str(e)}")

@router.post("/uvgs/calculate", response_model=UBGRUVGRResponse)
@limiter.limit("30/minute")
def calculate_uvgs_premium(
    request: Request,
    payload: UBGRUVGRRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate premium for UVGS (United Value Griha Suraksha) product.
    
    **Key Difference from UBGR/UVGR:**
    - Terrorism Premium is NOT applicable
    - Otherwise follows same calculation logic
    """
    try:
        logger.info(f"UVGS Premium Calculation Request: {payload.model_dump()}")
        
        # Override product code to ensure UVGS
        payload.productCode = "UVGS"
        
        result = FirePremiumCalculator.calculate_ubgr_uvgr(payload)
        return UBGRUVGRResponse(**result)
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calculation Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Premium calculation failed: {str(e)}")
