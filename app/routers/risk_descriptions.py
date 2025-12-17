from fastapi import APIRouter, Depends, Query
import logging
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.fire_models import Occupancy

router = APIRouter(
    tags=["Risk Descriptions"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.options("/api/risk-descriptions")
async def risk_descriptions_options():
    logger.info("OPTIONS preflight for /api/risk-descriptions")
    return {}

@router.get("/api/risk-descriptions")
def get_risk_descriptions(
    productCode: str = Query(..., description="Product Code (e.g., UBGR, BGRP, UVGR)"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"GET /api/risk-descriptions?productCode={productCode}")
        
        query = db.query(Occupancy)
        occupancies = query.order_by(Occupancy.risk_description).all()
        
        logger.info(f"Returning {len(occupancies)} risk descriptions")
        
        return {
            "success": True,
            "data": [
                {
                    "occupancy_code": occ.occupancy_code,
                    "occupancy_description": occ.risk_description,
                    "occupancy_type": occ.occupancy_type,
                    "aift_section": occ.section_aift,
                    "iib_code": occ.iib_code,
                }
                for occ in occupancies
            ]
        }
    
    except Exception as e:
        logger.error(f"Error in /api/risk-descriptions: {e}", exc_info=True)
        return {
            "success": False,
            "message": str(e),
            "data": []
        }
