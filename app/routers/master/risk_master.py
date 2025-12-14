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

@router.get("/master/risk-descriptions", response_model=List[RiskDescriptionResponse])
def get_risk_descriptions(
    productCode: str = Query(..., description="Product Code to filter risks"),
    db: Session = Depends(get_db)
):
    """
    Get Risk Descriptions (Occupancies) filtered by Product Code.
    
    Business Rules:
    - BGRP, UVGR: Return Dwellings (1001) and Co-op (1001_2) ONLY.
    - BSUS, BLUS, UVUS, SFSP, IAR: Return ALL remaining risks (Non-Residential).
    
    Includes aliases (e.g. BSUSP, BLUSP) for robustness.
    """
    try:
        product_code_upper = productCode.upper().strip()
        
        # 1. Normalize BGRP -> UBGR
        if product_code_upper == "BGRP":
            product_code_upper = "UBGR"
            
        # Valid Product Codes & Aliases
        # Group A: Residential
        GROUP_A = {'UBGR', 'UVGR', 'UVGS'} 
        
        # Group B: Commercial / Others
        GROUP_B = {'BSUS', 'BLUS', 'UVUS', 'SFSP', 'IAR', 'BSUSP', 'BLUSP', 'VUSP'} 
        
        query = db.query(Occupancy)
        risks = []
        
        if product_code_upper in GROUP_A:
            # Residential: Only Dwellings and Co-op Housing Society
            # iib_code = 1001, 1001_2
            risks = query.filter(Occupancy.iib_code.in_(['1001', '1001_2'])).all()
            
        elif product_code_upper in GROUP_B:
             # Commercial: All except 1001 and 1001_2
             risks = query.filter(Occupancy.iib_code.notin_(['1001', '1001_2'])).all()
             
        else:
            # Unknown product code -> Return empty list as per strict requirement
            logger.warning(f"Unknown productCode received: {productCode}")
            return []
            
        results = []
        for r in risks:
            if not r: continue
            results.append(RiskDescriptionResponse(
                riskDescription=r.risk_description,
                iibCode=r.iib_code,
                aiftSection=_to_roman_safe(r.section_aift),
                occupancyType=r.occupancy_type
            ))
            
        return results
        
    except Exception as e:
        logger.error(f"Error serving risk descriptions for {productCode}: {e}", exc_info=True)
        return []
