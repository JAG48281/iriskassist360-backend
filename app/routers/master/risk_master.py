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
        product_code_input = productCode
        product_code_upper = productCode.upper().strip()
        
        # 1. Normalize Aliases to Canonical Codes
        if product_code_upper == "UBGR":
            normalized_code = "BGRP"
        elif product_code_upper == "UVGR":
            normalized_code = "UVUS"
        elif product_code_upper == "BLGR":
            normalized_code = "BLUS"
        else:
            normalized_code = product_code_upper
            
        # 2. Define Groups based on CANONICAL codes
        # Group A: Residential (Dwellings)
        GROUP_A = {'BGRP', 'UVGS'} 
        
        # Group B: Commercial / Others
        GROUP_B = {'BSUS', 'BLUS', 'UVUS', 'SFSP', 'IAR', 'BSUSP', 'BLUSP', 'VUSP'} 
        
        query = db.query(Occupancy)
        risks = []
        
        if normalized_code in GROUP_A:
            # Residential: Only Dwellings and Co-op Housing Society
            # occupancy_code (iib_code) = 1001, 1001_2
            risks = query.filter(Occupancy.iib_code.in_(['1001', '1001_2'])).all()
            
        elif normalized_code in GROUP_B:
             # Commercial: All except 1001 and 1001_2
             risks = query.filter(Occupancy.iib_code.notin_(['1001', '1001_2'])).all()
             
        else:
            # Unknown product code -> Return empty list as per strict requirement
            logger.warning(f"Unknown productCode received: {productCode} (normalized: {normalized_code})")
            return []
            
        results = []
        for r in risks:
            if not r: continue
            results.append(RiskDescriptionResponse(
                occupancyId=r.id,
                occupancyCode=r.iib_code,
                occupancyDescription=r.risk_description,
                aiftSection=_to_roman_safe(r.section_aift),
                occupancyType=r.occupancy_type
            ))
            
        logger.info("Risk descriptions fetched for productCode=%s (normalized=%s), count=%d", product_code_input, normalized_code, len(results))
        return results
        
    except Exception as e:
        logger.error(f"Error serving risk descriptions for {productCode}: {e}", exc_info=True)
        return []
