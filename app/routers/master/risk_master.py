from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.fire_models import Occupancy
from app.schemas.master import RiskDescriptionResponse

router = APIRouter(
    tags=["Master Data"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

def _to_roman_safe(val: str) -> str:
    """Ensure Section is Roman Numeral. Handles '1'->'I', etc."""
    val = val.replace('Section', '').replace('section', '').strip()
    
    mapping = {
        "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
        "6": "VI", "7": "VII", "8": "VIII"
    }
    return mapping.get(val, val)

def normalize_fire_product_code(code: str) -> str:
    code = code.upper().strip()
    mapping = {
        "UBGR": "BGRP",
        "UVGR": "UVUS",
        "BLGR": "BLUS"
    }
    return mapping.get(code, code)

@router.get("/master/risk-descriptions")
def get_risk_descriptions(
    productCode: str = Query(..., description="Product Code"),
    db: Session = Depends(get_db)
):
    """
    Get risk descriptions for a given product code.
    
    **Product Normalization**:
    - UBGR → BGRP
    - UVGR → UVUS
    - BLGR → BLUS
    
    **Filtering Rules**:
    - BGRP: Only residential dwellings (IIB codes 1001, 1001_2)
    - Other products: Exclude residential dwellings
    
    **Response Format**:
    ```json
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "description": "Dwellings",
                "occupancy_type": "Residential",
                "aift_section": "III",
                "iib_code": "1001"
            }
        ]
    }
    ```
    """
    try:
        logger.info(f"📋 Risk descriptions request for productCode={productCode}")
        
        # Normalize product code (UBGR → BGRP)
        normalized = normalize_fire_product_code(productCode)
        logger.info(f"📋 Normalized product code: {productCode} → {normalized}")

        query = db.query(Occupancy)
        # Note: Occupancy table does not have is_active column, skipping filter.
        # query = query.filter(Occupancy.is_active == True)

        # UBGR / BGRP → ONLY residential dwellings (IIB codes 1001, 1001_2)
        if normalized == "BGRP":
            query = query.filter(
                Occupancy.iib_code.in_(["1001", "1001_2"])
            )
            logger.info("📋 Filtering for BGRP: IIB codes 1001, 1001_2")

        # ALL OTHER FIRE PRODUCTS - exclude residential dwellings
        else:
            query = query.filter(
                Occupancy.iib_code.notin_(["1001", "1001_2"])
            )
            logger.info(f"📋 Filtering for {normalized}: Excluding IIB codes 1001, 1001_2")

        risks = query.order_by(Occupancy.risk_description).all()
        
        logger.info(f"✅ Found {len(risks)} risk descriptions for {normalized}")

        # ALWAYS return success with data array (even if empty)
        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "description": r.risk_description,
                    "occupancy_type": r.occupancy_type,
                    "aift_section": _to_roman_safe(r.section_aift),
                    "iib_code": r.iib_code,
                }
                for r in risks
            ]
        }

    except Exception as e:
        logger.error(f"❌ Error serving risk descriptions: {e}", exc_info=True)
        # NEVER throw - always return valid JSON
        return {
            "success": False,
            "message": str(e),
            "data": []  # Return empty array on error
        }

