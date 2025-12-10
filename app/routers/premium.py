import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rate import Rate
from app.schemas.response import ResponseModel
from app.schemas.uvgs_schema import UVGSRequest

# Setup Logger
logger = logging.getLogger("irisk_backend")

router = APIRouter(prefix="/api/premium", tags=["Premium Calculation"])

@router.post("/uvgs/calculate", response_model=ResponseModel[dict])
def calculate_uvgs_premium(payload: UVGSRequest, db: Session = Depends(get_db)):
    logger.info(f"Calculating UVGS Premium for: {payload}")
    
    # Placeholder Logic
    # 1. Base Rate (e.g., 1% of SI)
    base_rate = 0.01
    
    # 2. Tenure Multiplier
    tenure_multiplier = 1.0
    if payload.policy_tenure > 1:
        # Simple discount logic for long term
        tenure_multiplier = 1.0 - (0.05 * (payload.policy_tenure - 1))
        
    # 3. Calculate
    base_premium = payload.sum_insured * base_rate * payload.member_count * payload.policy_tenure * tenure_multiplier
    
    # 4. Tax
    gst = base_premium * 0.18
    total_premium = base_premium + gst
    
    data = {
        "base_premium": round(base_premium, 2),
        "gst": round(gst, 2),
        "total_premium": round(total_premium, 2),
        "input_summary": payload.dict()
    }
    
    return ResponseModel(success=True, message="UVGS Premium Calculated Successfully", data=data)
