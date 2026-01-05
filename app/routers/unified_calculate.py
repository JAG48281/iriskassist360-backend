from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging
from app.services.rating_engine import get_terrorism_rate_per_mille
from fastapi.responses import JSONResponse
from fastapi import APIRouter
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Calculation"])

from typing import Optional


PRODUCT_CODE_MAP = {
    "UBGR": "bgrp",
    "ubgr": "bgrp",
}

class CalculateRequest(BaseModel):
    occupancyId: Optional[int] = None
    productCode: str
    iib_code: Optional[str] = None
    total_si: Optional[float] = None
    risk_rate: Optional[float] = Field(None, alias="risk_rate_per_mille")
    
    # New fields for detailed calculation with aliases to support UI camelCase
    # Aliases allows both snake_case (internal) and camelCase (external)
    basic_cover_si: Optional[float] = Field(0.0, alias="buildingSI")
    add_on_cover_si: Optional[float] = Field(0.0, alias="addOnCoverSI") # Mapped to contentsSI in adapter
    
    # Granular SIs for Strict UBGR
    loss_of_rent_si: Optional[float] = Field(0.0, alias="lossOfRentSI")
    alt_accommodation_si: Optional[float] = Field(0.0, alias="altAccommodationSI")
    valuable_contents_si: Optional[float] = Field(0.0, alias="valuableContentsSI")
    
    # PA Fields
    pa_proposer_si: Optional[float] = Field(0.0, alias="paProposerSI")
    pa_spouse_si: Optional[float] = Field(0.0, alias="paSpouseSI")
    pa_proposer_selected: Optional[bool] = Field(False, alias="paProposer")
    pa_spouse_selected: Optional[bool] = Field(False, alias="paSpouse")
    
    discountPercent: Optional[float] = 0.0
    loadingPercent: Optional[float] = 0.0
    terrorism_si: Optional[float] = Field(None, alias="terrorismSI")
    terrorism_rate: Optional[float] = Field(None, alias="terrorism_rate_per_mille")
    
    # Add-Ons List for checking 'TERRORISM' etc
    add_ons: Optional[list] = Field(default_factory=list, alias="addOns")

    class Config:
        populate_by_name = True

    @validator('productCode')
    def validate_product_code(cls, v):
        # Normalize product_code
        v_clean = v.strip().lower()
        # Resolver
        canonical = PRODUCT_CODE_MAP.get(v_clean.upper(), v_clean)
        
        if canonical not in ["bgrp"]:
             raise ValueError(f"Invalid product code. Must be BGRP/UBGR, got {v}")
        return canonical

@router.post("/calculate")
async def calculate_risk_rate(request: CalculateRequest):
    """
    Calculate risk rate and premium for Fire (UBGR) product.
    Delegates to authoritative FirePremiumCalculator.
    """
    try:
        logger.info(f"🧮 Calculate request: productCode={request.productCode}")
        
        # Product Code is already normalized by validator to 'bgrp'
        product_code = request.productCode
        
        if product_code == "bgrp":
            logger.info(f"UBGR normalized to canonical product code: {product_code}")
            
            from app.schemas.fire_premium import UBGRUVGRRequest, PASelection, AddOnItem
            from app.services.fire_premium_service import FirePremiumCalculator
            
            # Step 1: Validate iib_code
            if not request.iib_code:
                logger.error("iib_code missing for BGRP calculation")
                return JSONResponse(
                   status_code=422,
                   content={"error": "iib_code required", "success": False}
                )

            iib_code = request.iib_code.strip()
            
            # MANDATORY Rule: Use only risk_rate from request
            if request.risk_rate is None:
                 logger.error("risk_rate missing for BGRP calculation - Must be explicitly provided")
                 return JSONResponse(
                    status_code=422,
                    content={"error": "risk_rate required for BGRP calculation", "success": False}
                 )
            
            # Adapter: Map CalculateRequest -> UBGRUVGRRequest
            # Handle Add-ons list conversion
            schema_addons = []
            if request.add_ons:
                for a in request.add_ons:
                    if isinstance(a, dict):
                        schema_addons.append(AddOnItem(addOnCode=a.get('addOnCode', ''), sumInsured=a.get('sumInsured', 0)))
                    elif isinstance(a, str):
                         schema_addons.append(AddOnItem(addOnCode=a, sumInsured=0))
            
            # Setup PA Selection
            pa_sel = PASelection(
                proposer=request.pa_proposer_selected,
                spouse=request.pa_spouse_selected
            )
            
            # Create Authoritative Payload
            ubgr_payload = UBGRUVGRRequest(
                productCode="UBGR", # Force UBGR for calculator
                occupancyCode=iib_code,
                buildingSI=request.basic_cover_si,
                contentsSI=request.add_on_cover_si, # Mapping addOnCoverSI to contentsSI
                
                lossOfRentSI=request.loss_of_rent_si,
                altAccommodationSI=request.alt_accommodation_si,
                valuableContentsSI=request.valuable_contents_si,
                
                paProposerSI=request.pa_proposer_si,
                paSpouseSI=request.pa_spouse_si,
                paSelection=pa_sel,
                
                terrorism_si=request.terrorism_si if request.terrorism_si is not None else 0.0,
                
                addOns=schema_addons, # Pass add-ons mainly for TERRORISM flags
                
                discountPercentage=request.discountPercent,
                loadingPercentage=request.loadingPercent,
                
                risk_rate_per_mille=request.risk_rate # Pass explicit rate
            )
            
            # Call Service
            logger.info("Delegating to FirePremiumCalculator...")
            result = FirePremiumCalculator.calculate_ubgr_uvgr(ubgr_payload)
            
            # Map Result to Response (Merging meta)
            # result is a Dict from the service
            
            # Extract fields for direct compatibility with UI expectations
            data = {
                "basic_fire_premium": result["basic_fire_premium"],
                "add_on_premium": result["add_on_premium"],
                "discount_amount": result["discount_amount"],
                "loading_amount": result["loading_amount"],
                "subtotal_premium": result["subtotal_premium"],
                "terrorism_premium": result["terrorism_premium"],
                "net_premium": result["net_premium"],
                "cgst": result["cgst"],
                "sgst": result["sgst"],
                "stamp_duty": result["stamp_duty"],
                "gross_premium": result["gross_premium"],
                
                # Extended Fields
                "total_property_si": result.get("total_property_si", 0),
                "pa_proposer_premium": result.get("pa_proposer_premium", 0),
                "pa_spouse_premium": result.get("pa_spouse_premium", 0),
                "terrorism_si": result.get("terrorism_si", 0),
                
                # Extra metadata
                "fire_premium": result["subtotal_premium"], # Legacy alias
                "risk_rate_used": request.risk_rate,
                "terrorism_rate_used": result.get("meta", {}).terrorism_rate if hasattr(result.get("meta"), "terrorism_rate") else 0,
                "product_code": "bgrp",
                "calculated_at": datetime.now().isoformat()
            }
            
            return data
        
        # Legacy/Other Products Logic (if any)
        logger.warning(f"Product {product_code} not fully supported in unified calculate yet")
        return JSONResponse(
            status_code=400,
            content={"error": f"Product {product_code} not supported", "success": False}
        )
        
    except Exception as e:
        logger.error(f"🔥 Error in calculate endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal server error: {str(e)}",
                "meta": {"risk_rate": None}
            }
        )
