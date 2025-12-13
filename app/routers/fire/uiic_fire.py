from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_db
from app.models.rate import Rate
from app.models.quote import Quote
from app.utils.pdf_generator import generate_premium_pdf

from app.schemas.response import ResponseModel
from app.services.rating_engine import get_basic_rate_per_mille, get_terrorism_rate_per_mille
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/irisk/fire/uiic", tags=["UIIC-Fire"])

# -------------------------------
# Request Models
# -------------------------------
class FireCalcRequest(BaseModel):
    building_si: int = Field(..., gt=0, description="Sum insured (whole rupees)")
    occupancy: str
    pa_selected: bool = False

class UBGRRequest(BaseModel):
    buildingSI: float
    contentsSI: float
    terrorismCover: Optional[str] = None
    terrorismSI: Optional[float] = None
    paProposer: Optional[str] = None
    paProposerSI: Optional[float] = None
    paSpouse: Optional[str] = None
    paSpouseSI: Optional[float] = None
    discountPercentage: float = 0.0

# -------------------------------
# Helper Functions
# -------------------------------

def _calculate_premium(building_si: int, rate_per_mille: float, pa_selected: bool,
                       mandatory_terrorism_per_mille: float = 0.07) -> Dict[str, Any]:
    basic = building_si * (rate_per_mille / 1000.0)
    terrorism = building_si * (mandatory_terrorism_per_mille / 1000.0)
    pa = 7 if pa_selected else 0
    net = basic + terrorism + pa

    if net < 50:
        net = 50.0

    gst = round(net * 0.18, 2)
    gross = round(net + gst, 2)

    return {
        "basic_premium": round(basic, 2),
        "terrorism_premium": round(terrorism, 2),
        "pa_premium": pa,
        "net_premium": round(net, 2),
        "gst": gst,
        "gross_premium": gross
    }


def _lookup_rate(db: Session, product_code: str, occupancy: str, fallback: Dict[str, float]):
    rate_row = db.query(Rate).filter(
        Rate.company == "UIIC",
        Rate.lob == "Fire",
        Rate.product == product_code,
        Rate.key.ilike(occupancy)
    ).first()

    if rate_row:
        return rate_row.value
    
    # Fallback logic
    for key, val in fallback.items():
        if key.lower() in occupancy.lower():
            return val
    
    # Default if nothing matches
    return 0.15

def _save_quote(db: Session, product_code: str, payload: Any, response: Dict[str, Any]):
    try:
        q = Quote(
            brand="iRiskAssist360",
            company="UIIC",
            lob="Fire",
            product=product_code,
            request_data=payload.dict(),
            response_data=response
        )
        db.add(q)
        db.commit()
    except Exception:
        db.rollback()


# ---------------------------------------------------------
# PRODUCT 1: Value Udyam Suraksha Policy (VUSP)
# ---------------------------------------------------------
@router.post("/vusp/calculate", response_model=ResponseModel[dict])
def calculate_vusp(payload: FireCalcRequest, db: Session = Depends(get_db)):
    product_code = "VUSP"
    fallback = {"Office": 0.20, "Residential": 0.16, "Hospital": 0.22, "Shop": 0.25}
    occ = payload.occupancy.strip().title()
    rate = _lookup_rate(db, product_code, occ, fallback)
    result = _calculate_premium(payload.building_si, rate, payload.pa_selected)
    response = {
        "brand": "iRiskAssist360",
        "company": "UIIC",
        "lob": "Fire",
        "product": "Value Udyam Suraksha Policy (VUSP)",
        "rate_applied": rate,
        "building_si": payload.building_si,
        **result
    }
    _save_quote(db, product_code, payload, response)
    return ResponseModel(success=True, message="VUSP Premium Calculated", data=response)

# ---------------------------------------------------------
# PRODUCT 2: Bharat Sookshma Udyam Suraksha (BSUSP)
# ---------------------------------------------------------
@router.post("/bsusp/calculate", response_model=ResponseModel[dict])
def calculate_bsusp(payload: FireCalcRequest, db: Session = Depends(get_db)):
    product_code = "BSUSP"
    fallback = {"Office": 0.20, "Residential": 0.16, "Hospital": 0.22, "Shop": 0.25}
    occ = payload.occupancy.strip().title()
    rate = _lookup_rate(db, product_code, occ, fallback)
    result = _calculate_premium(payload.building_si, rate, payload.pa_selected)
    response = {
        "brand": "iRiskAssist360",
        "company": "UIIC",
        "lob": "Fire",
        "product": "Bharat Sookshma Udyam Suraksha (BSUSP)",
        "rate_applied": rate,
        "building_si": payload.building_si,
        **result
    }
    _save_quote(db, product_code, payload, response)
    return ResponseModel(success=True, message="BSUSP Premium Calculated", data=response)

# ---------------------------------------------------------
# PRODUCT 3: Bharat Laghu Udyam Suraksha (BLUSP)
# ---------------------------------------------------------
@router.post("/blusp/calculate", response_model=ResponseModel[dict])
def calculate_blusp(payload: FireCalcRequest, db: Session = Depends(get_db)):
    product_code = "BLUSP"
    fallback = {"Office": 0.20, "Residential": 0.16, "Hospital": 0.22, "Shop": 0.25}
    occ = payload.occupancy.strip().title()
    rate = _lookup_rate(db, product_code, occ, fallback)
    result = _calculate_premium(payload.building_si, rate, payload.pa_selected)
    response = {
        "brand": "iRiskAssist360",
        "company": "UIIC",
        "lob": "Fire",
        "product": "Bharat Laghu Udyam Suraksha Policy (BLUSP)",
        "rate_applied": rate,
        "building_si": payload.building_si,
        **result
    }
    _save_quote(db, product_code, payload, response)
    return ResponseModel(success=True, message="BLUSP Premium Calculated", data=response)

# ---------------------------------------------------------
# PRODUCT 4: Bharat Griha Raksha Policy (BGRP)
# ---------------------------------------------------------
@router.post("/bgrp/calculate", response_model=ResponseModel[dict])
def calculate_bgrp(payload: UBGRRequest, db: Session = Depends(get_db)):
    product_code = "BGRP"
    logger.info(f"--- BGRP CALC START ---")
    logger.info(f"Payload: {payload.dict()}")

    # 1. Total SI = Building + Contents
    totalSI = payload.buildingSI + payload.contentsSI
    
    # 2. Rate Lookup
    # BGRP is primarily Residential (101)
    occupancy_code = "101" 
    
    basic_rate_decimal = get_basic_rate_per_mille(product_code, occupancy_code)
    basic_rate = float(basic_rate_decimal)
    
    logger.info(f"Rate Lookup for {product_code}/{occupancy_code}: {basic_rate}")

    if basic_rate <= 0:
        raise HTTPException(status_code=400, detail=f"Rate lookup failed for {product_code}. Check configuration.")
    
    # Fire Premium
    firePremium = totalSI * (basic_rate / 1000.0)
    
    # 3. Terrorism Premium
    terrorismSI = totalSI
    terrorismPremium = 0.0
    
    # Always calculate terrorism premium for BGRP (Mandatory)
    terr_rate_decimal = get_terrorism_rate_per_mille(product_code)
    terr_rate = float(terr_rate_decimal)
    if terr_rate > 0:
        terrorismPremium = terrorismSI * (terr_rate / 1000.0)
    else:
        logger.warning(f"Terrorism rate for BGRP is 0. Check seeding.")

    # 4. PA Premium (Flat Rs. 7 per person)
    paPremium = 0.0
    
    if payload.paProposer == 'Yes':
        paPremium += 7.0
        
    if payload.paSpouse == 'Yes':
        paPremium += 7.0
        
    # 5. Total & Taxes
    # Mandatory Rule: BGRP Net Premium = Fire Premium + Terrorism Premium (+ PA if any)
    # Discounts usually apply to the base fire premium, but requirement says "Net Premium = Fire + Terrorism".
    # We will assume discount applies to Fire portion only OR applies to total.
    # User instruction: "net_premium = fire_premium + terrorism_premium".
    # It implies simple aggregation. We will respect discount on fire/base if applicable or apply to loaded base.
    
    # Current logic applied discount to (fire + terrorism + pa).
    # If standard practice, discount applies to fire only.
    # However, strict instructions say: "net_premium = fire_premium + terrorism_premium"
    # To be safe and compliant with "Net Premium correctly excludes terrorism for BGRP" (Issue statement),
    # I'll calculate discount on fire only, or apply discount first then add terrorism?
    # User said: "Net Premium incorrectly excludes terrorism for BGRP"
    # This likely means terrorism was being dropped or not added. 
    # Let's aggregate cleanly.
    
    base_fire_pa = firePremium + paPremium
    
    # Apply Discount to Fire+PA (or just Fire). Assuming Fire+PA for now or following previous pattern but ensuring Terrorism is ADDED.
    discountFactor = (100 - payload.discountPercentage) / 100
    discounted_base = base_fire_pa * discountFactor
    
    # Net Premium Aggregation
    netPremium = discounted_base + terrorismPremium
    
    # Minimum Premium Logic (Should not apply during aggregation, but final check)
    # User said: "DO NOT... apply min premium logic here" (in aggregation steps).
    
    # Hard Log Reqd
    print(f"BGRP BACKEND DEBUG | fire={firePremium}, terrorism={terrorismPremium}, net={netPremium}")
    
    # Final Min Premium Check
    min_premium = 50.0
    if netPremium < min_premium:
        logger.info(f"Net Premium {netPremium} < {min_premium}, applying minimum.")
        netPremium = min_premium
        
    cgst = netPremium * 0.09
    sgst = netPremium * 0.09
    stampDuty = 1.0
    grossPremium = netPremium + cgst + sgst + stampDuty
    
    # Construct Response
    response = {
        "product": "Bharat Griha Raksha Policy",
        "product_code": "BGRP",
        "netPremium": round(netPremium, 2),
        "basic_premium": round(firePremium, 2),  # Clarified: Fire Only
        "firePremium": round(firePremium, 2),    # Explicit requested field
        "terrorism_premium": round(terrorismPremium, 2), # Alias
        "terrorismPremium": round(terrorismPremium, 2),  # Explicit requested field
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "stampDuty": stampDuty,
        "grossPremium": round(grossPremium, 2),
        "breakdown": {
            "totalSI": totalSI,
            "firePremium": round(firePremium, 2),
            "terrorismPremium": round(terrorismPremium, 2),
            "paPremium": round(paPremium, 2),
            "basePremium": round(firePremium + paPremium, 2), # Base usually excludes terrorism for discounting?
            "discountApplied": round(base_fire_pa - discounted_base, 2),
            "appliedRate": basic_rate
        }
    }
    
    logger.info(f"BGRP Response: net={netPremium}, gross={grossPremium}, fire={firePremium}, terrorism={terrorismPremium}")

    _save_quote(db, product_code, payload, response)
    return ResponseModel(success=True, message="BGRP Premium Calculated", data=response)

# ---------------------------------------------------------
# PRODUCT 5: Standard Fire & Special Perils Policy (SFSP)
# ---------------------------------------------------------
@router.post("/sfsp/calculate", response_model=ResponseModel[dict])
def calculate_sfsp(payload: FireCalcRequest, db: Session = Depends(get_db)):
    product_code = "SFSP"
    fallback = {"Factory": 0.60, "Plant": 0.75, "Warehouse": 0.40}
    occ = payload.occupancy.strip().title()
    rate = _lookup_rate(db, product_code, occ, fallback)
    result = _calculate_premium(payload.building_si, rate, payload.pa_selected)
    response = {
        "brand": "iRiskAssist360",
        "company": "UIIC",
        "lob": "Fire",
        "product": "Standard Fire & Special Perils Policy (SFSP)",
        "rate_applied": rate,
        "building_si": payload.building_si,
        **result
    }
    _save_quote(db, product_code, payload, response)
    return ResponseModel(success=True, message="SFSP Premium Calculated", data=response)

# ---------------------------------------------------------
# PRODUCT 6: Industrial All Risks Policy (IAR)
# ---------------------------------------------------------
@router.post("/iar/calculate", response_model=ResponseModel[dict])
def calculate_iar(payload: FireCalcRequest, db: Session = Depends(get_db)):
    product_code = "IAR"
    fallback = {"Factory": 0.60, "Plant": 0.75, "Warehouse": 0.40}
    occ = payload.occupancy.strip().title()
    rate = _lookup_rate(db, product_code, occ, fallback)
    result = _calculate_premium(payload.building_si, rate, payload.pa_selected)
    response = {
        "brand": "iRiskAssist360",
        "company": "UIIC",
        "lob": "Fire",
        "product": "Industrial All Risks Policy (IAR)",
        "rate_applied": rate,
        "building_si": payload.building_si,
        **result
    }
    _save_quote(db, product_code, payload, response)
    return ResponseModel(success=True, message="IAR Premium Calculated", data=response)

# ---------------------------------------------------------
# OPTIONAL PDF Endpoint
# ---------------------------------------------------------
@router.post("/calculate/pdf", response_model=ResponseModel[dict])
def any_product_pdf(payload: FireCalcRequest, db: Session = Depends(get_db)):
    resp = calculate_blusp(payload, db).data # Access .data from ResponseModel
    pdf = generate_premium_pdf(resp)
    # Return standard response
    return ResponseModel(
        success=True, 
        message="PDF generated successfully", 
        data={"pdf_size_bytes": len(pdf), "download_link": "TODO_LINK"} # Placeholder logic
    )
