
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

from app.models.fire_models import FireIibRate

@router.get("/api/fire/risk-rate")
def get_risk_rate(
    iib_code: str = Query(..., description="IIB Code"),
    db: Session = Depends(get_db)
):
    """
    Get Fire Risk Rate strictly from fire_iib_rates.
    Product Agnostic: BLUS, UVUS, SFSP, IAR, BGRP.
    """
    code_str = str(iib_code).strip()
    
    rate_val = get_fire_risk_rate(code_str, db)
    
    # Logging (MANDATORY)
    logger.info(
      f"[FIRE RISK RATE] iib_code={code_str} → rate={rate_val}"
    )

    return {
        "iib_code": code_str,
        "risk_rate_per_mille": rate_val
    }

def get_fire_risk_rate(iib_code: str, db: Session) -> float:
    """
    Unified Resolver: Fetch rate strictly from fire_iib_rates.
    """
    rate_row = (
        db.query(FireIibRate)
        .filter(FireIibRate.iib_code == iib_code)
        .first()
    )

    if not rate_row:
        logger.warning(f"Risk rate not found for IIB code {iib_code}")
        raise HTTPException(
            status_code=404,
            detail=f"Risk rate not found for IIB code {iib_code}"
        )

    return float(rate_row.rate_per_mille)

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
