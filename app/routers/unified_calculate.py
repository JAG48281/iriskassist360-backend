from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services.rating_engine import get_basic_rate_per_mille
from app.schemas.response import ResponseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Calculation"])

class CalculateRequest(BaseModel):
    occupancy_id: int = Field(..., description="Occupancy ID (Integer)")
    product_code: str = Field(..., description="Product Code (e.g. BGRP)") 
    eq_zone: Optional[str] = Field(None, description="EQ Zone (Required for BSUS)")
    
    building_si: Optional[float] = 0.0
    contents_si: Optional[float] = 0.0

@router.post("/calculate", response_model=ResponseModel[dict])
async def calculate_risk_rate(request: CalculateRequest):
    """
    Unified calculation endpoint. 
    Can be used for:
    1. Risk Rate Lookup (provide occupancy_id + product_code + optional eq_zone)
    2. Premium Calculation (provide SIs - functionality TBD/Proxied)
    """
    try:
        logger.info(f"🔥 Calculate Payload: {request.model_dump()}")
        logger.info(f"🔥 occupancy_id={request.occupancy_id} type={type(request.occupancy_id)}")
        
        # 1. Rate Lookup
        occ_id = request.occupancy_id
        prod_code = request.product_code.upper()
        eq_zone = request.eq_zone
        
        # Pass eq_zone to rate engine
        rate = float(get_basic_rate_per_mille(prod_code, occ_id, eq_zone=eq_zone))
        
        # 2. Risk Rate Meta Construction
        meta = {
            "risk_rate": rate,
            "product_code": prod_code,
            "occupancy_code": str(occ_id)
        }
        
        # 3. Premium Calculation (Placeholder)
        return ResponseModel(
            success=True,
            message="Risk Rate Fetched",
            data={
                "meta": meta,
                "breakdown": {},
                "net_premium": 0.0, 
                "gross_premium": 0.0
            }
        )
        
    except ValueError as e:
        logger.error(f"Calculation validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unified calculation error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
