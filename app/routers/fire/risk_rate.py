
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
