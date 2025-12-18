
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.rating_engine import get_terrorism_rate_per_mille
import logging

router = APIRouter(
    tags=["Fire Rating"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

from sqlalchemy import text

@router.get("/api/fire/risk-rate")
def get_risk_rate(
    iib_code: str = Query(..., description="IIB Code"),
    db: Session = Depends(get_db)
):
    """
    Get Fire Risk Rate strictly from fire_iib_rates.
    Product Agnostic by design: BLUS, UVUS, SFSP, IAR, BGRP.
    """
    code_str = str(iib_code).strip()
    
    rate_val = get_fire_risk_rate(code_str, db)
    
    # ❌ If no row → return 404 with clear message
    if rate_val is None:
        logger.warning(f"No risk rate found in fire_iib_rates for iib_code={code_str}")
        raise HTTPException(
            status_code=404, 
            detail=f"Risk rate not found for IIB code {code_str}"
        )

    # Mandatory Log (as per requirement)
    logger.info(f"Fetching base risk rate from fire_iib_rates for iib_code={code_str}")

    return {
        "iib_code": code_str,
        "risk_rate_per_mille": rate_val
    }

def get_fire_risk_rate(iib_code: str, db: Session) -> float | None:
    """
    Unified Resolver: Fetch rate strictly from fire_iib_rates.
    Returns value or None.
    Uses MANDATORY RAW SQL.
    """
    # 3️⃣ BACKEND LOGIC (MANDATORY SQL EQUIVALENT)
    # rate = db.query(FireIIBRate).filter(FireIIBRate.iib_code == iib_code).first()
    # Implemented via RAW SQL for reliability as per previous context.
    
    query = text("""
        SELECT rate_per_mille
        FROM fire_iib_rates
        WHERE iib_code = :iib_code
        LIMIT 1
    """)
    
    result = db.execute(query, {"iib_code": iib_code}).fetchone()

    if not result:
        logger.warning(f"[IIB RATE FETCH] iib_code={iib_code} rate=NOT_FOUND")
        return None

    rate = float(result.rate_per_mille)
    
    # 🧪 MANDATORY DEBUG LOG
    logger.info(f"[IIB RATE FETCH] iib_code={iib_code} rate={rate}")
    
    return rate

@router.get("/fire/terrorism-rate")
def get_terrorism_rate(
    occupancy_type: str = Query(..., description="Occupancy Type (Residential, Industrial, etc.)"),
    total_sum_insured: float = Query(..., description="Total Sum Insured"),
    db: Session = Depends(get_db)
):
    """
    Get Terrorism Rate based on Occupancy Type and Total SI.
    Strictly Product-Agnostic.
    """
    try:
        rate = get_terrorism_rate_per_mille(occupancy_type, total_sum_insured)
        return {
            "occupancy_type": occupancy_type,
            "total_sum_insured": total_sum_insured,
            "terrorism_rate_per_mille": float(rate)
        }
    except ValueError as e:
        logger.error(f"Terrorism lookup error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
