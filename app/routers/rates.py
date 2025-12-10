import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rate import Rate
from app.schemas.response import ResponseModel

# Setup Logger
logger = logging.getLogger("irisk_backend")

router = APIRouter(prefix="/api/rates", tags=["Rates"])

@router.get("/ubgr", response_model=ResponseModel[List[Dict[str, Any]]])
def get_ubgr_rates(db: Session = Depends(get_db)):
    logger.info("Fetching UBGR Rates")
    
    # Fetch from DB where product='BGRP' (Bharat Griha Raksha Policy)
    rates = db.query(Rate).filter(Rate.product == "BGRP").all()
    
    if not rates:
        # Return static mock if DB is empty for demo
        mock_data = [
            {"category": "Building", "key": "AgreedValue", "value": 0.15},
            {"category": "Contents", "key": "AgreedValue", "value": 0.15},
            {"category": "Terrorism", "key": "Mandatory", "value": 0.07},
        ]
        return ResponseModel(success=True, message="UBGR Rates (Static)", data=mock_data)
        
    data = [{"category": r.category, "key": r.key, "value": r.value} for r in rates]
    return ResponseModel(success=True, message="UBGR Rates", data=data)

@router.get("/uvgs", response_model=ResponseModel[List[Dict[str, Any]]])
def get_uvgs_rates(db: Session = Depends(get_db)):
    logger.info("Fetching UVGS Rates")
    
    # Fetch from DB
    rates = db.query(Rate).filter(Rate.product == "UVGS").all()
    
    if not rates:
         # Return static mock
        mock_data = [
            {"category": "AgeBand", "key": "18-35", "value": 1500.0},
            {"category": "AgeBand", "key": "36-45", "value": 2200.0},
            {"category": "TenureDiscount", "key": "2Year", "value": 5.0},
        ]
        return ResponseModel(success=True, message="UVGS Rates (Static)", data=mock_data)

    data = [{"category": r.category, "key": r.key, "value": r.value} for r in rates]
    return ResponseModel(success=True, message="UVGS Rates", data=data)
