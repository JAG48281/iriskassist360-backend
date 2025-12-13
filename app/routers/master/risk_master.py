from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.fire_models import Occupancy
from app.schemas.master import RiskDescriptionResponse

router = APIRouter(
    tags=["Master Data"],
    responses={404: {"description": "Not found"}},
)

@router.get("/master/risk-descriptions", response_model=List[RiskDescriptionResponse])
def get_risk_descriptions(
    productCode: str = Query(..., description="Product Code to filter risks"),
    db: Session = Depends(get_db)
):
    """
    Get Risk Descriptions (Occupancies) filtered by Product Code.
    
    Business Rules:
    - BGRP, UBGR, UVGR: Return Dwellings (1001) and Co-op (1001_2) ONLY.
    - BSUS, BLUS, UVUS, SFSP, IAR: Return ALL remaining risks (Non-Residential).
    """
    
    # Valid Product Codes
    GROUP_A = {'BGRP', 'UBGR', 'UVGR'} # Residential
    GROUP_B = {'BSUS', 'BLUS', 'UVUS', 'SFSP', 'IAR'} # Commercial/Others
    
    product_code_upper = productCode.upper()
    
    if product_code_upper not in GROUP_A and product_code_upper not in GROUP_B:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid productCode: {productCode}. Allowed: {', '.join(sorted(GROUP_A | GROUP_B))}"
        )
        
    query = db.query(Occupancy)
    
    if product_code_upper in GROUP_A:
        # Residential: Only Dwellings and Co-op Housing Society
        # iib_code = 1001, 1001_2
        risks = query.filter(Occupancy.iib_code.in_(['1001', '1001_2'])).all()
        
    else:
        # Commercial: All except 1001 and 1001_2
        risks = query.filter(Occupancy.iib_code.notin_(['1001', '1001_2'])).all()
        
    results = []
    for r in risks:
        # Clean up AIFT Section (defensive coding)
        # Expected: "I", "II", "III"
        # Stored might be "Section III"
        aift_cleaned = r.section_aift.replace('Section', '').replace('section', '').strip()
        
        results.append(RiskDescriptionResponse(
            riskDescription=r.risk_description,
            iibCode=r.iib_code,
            aiftSection=aift_cleaned,
            occupancyType=r.occupancy_type
        ))
        
    return results
