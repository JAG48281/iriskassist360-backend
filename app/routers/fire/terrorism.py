from fastapi import APIRouter, Query, HTTPException
from app.services.rating_engine import get_fire_terrorism_premium
import logging

router = APIRouter(
    prefix="/fire",
    tags=["Fire Terrorism"]
)

logger = logging.getLogger(__name__)

@router.get("/terrorism-premium")
async def calculate_terrorism_premium_api(
    occupancy_type: str = Query(..., description="Occupancy type (e.g., Residential, Industrial)"),
    total_si: float = Query(..., alias="total_si", description="Total Sum Insured")
):
    """
    Expose terrorism premium calculation as a standalone utility.
    (Objective 6)
    """
    try:
        premium = get_fire_terrorism_premium(occupancy_type, total_si)
        return {
            "terrorism_premium": round(premium, 2)
        }
    except Exception as e:
        logger.error(f"Error in terrorism premium API: {e}")
        raise HTTPException(status_code=400, detail=str(e))
