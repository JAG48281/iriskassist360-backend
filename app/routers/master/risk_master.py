from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
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

@router.get("/master/risk-descriptions")
def get_risk_descriptions(
    productCode: str = Query(..., description="Product Code to filter risks"),
    db: Session = Depends(get_db)
):
    """
    Get Risk Descriptions (Occupancies) filtered by Product Code.
    Returns standard API response: { "success": true, "data": [...] }
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
        GROUP_A = {'BGRP', 'UVGS'} 
        GROUP_B = {'BSUS', 'BLUS', 'UVUS', 'SFSP', 'IAR', 'BSUSP', 'BLUSP', 'VUSP'} 
        
        query = db.query(Occupancy)
        risks = []
        
        if normalized_code in GROUP_A:
            # Residential: Only Dwellings and Co-op Housing Society
            risks = query.filter(Occupancy.iib_code.in_(['1001', '1001_2'])).all()
        elif normalized_code in GROUP_B:
             # Commercial: All except 1001 and 1001_2
             risks = query.filter(Occupancy.iib_code.notin_(['1001', '1001_2'])).all()
        else:
            logger.warning(f"Unknown productCode: {productCode} (normalized: {normalized_code})")
            return {"success": True, "data": []}
            
        results = []
        for r in risks:
            if not r: continue
            results.append({
                "id": r.id,
                "description": r.risk_description,
                "iib_code": r.iib_code,
                "aift_section": _to_roman_safe(r.section_aift),
                "occupancy_type": r.occupancy_type
            })
            
        logger.info("Fetched risks for productCode=%s (norm=%s), count=%d", product_code_input, normalized_code, len(results))
        return {"success": True, "data": results}
        
    except Exception as e:
        logger.error(f"Error serving risk descriptions: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal Server Error", "error": str(e)}
        )
