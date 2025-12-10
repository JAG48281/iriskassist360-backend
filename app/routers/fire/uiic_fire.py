from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_db
from app.models.rate import Rate
from app.models.quote import Quote
from app.utils.pdf_generator import generate_premium_pdf

from app.schemas.response import ResponseModel

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
        Rate.occupancy.ilike(occupancy)
    ).first()

    if rate_row:
        return rate_row.rate_per_mille
    
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
    
    # 1. Total SI = Building + Contents
    totalSI = payload.buildingSI + payload.contentsSI
    
    # 2. Fire Premium (0.15 per mille)
    firePremium = totalSI * (0.15 / 1000.0)
    
    # 3. Terrorism Premium (0.07 per mille)
    # User Requirement: "Total SI = Terrorism SI"
    terrorismSI = totalSI
    terrorismPremium = 0.0
    if payload.terrorismCover == 'Yes':
        terrorismPremium = terrorismSI * (0.07 / 1000.0)
        
    # 4. PA Premium (Flat Rs. 7 per person)
    # User Requirement: "if user choose Yes, then premium is Flat rs. 7"
    paPremium = 0.0
    
    if payload.paProposer == 'Yes':
        paPremium += 7.0
        
    if payload.paSpouse == 'Yes':
        paPremium += 7.0
        
    # 5. Total & Taxes
    basePremium = firePremium + terrorismPremium + paPremium
    
    # Apply Discount
    discountFactor = (100 - payload.discountPercentage) / 100
    netPremium = basePremium * discountFactor
    
    # Minimum Premium Check
    if netPremium < 50:
        netPremium = 50.0
        
    cgst = netPremium * 0.09
    sgst = netPremium * 0.09
    stampDuty = 1.0
    grossPremium = netPremium + cgst + sgst + stampDuty
    
    response = {
        "netPremium": round(netPremium, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "stampDuty": stampDuty,
        "grossPremium": round(grossPremium, 2),
        "breakdown": {
            "totalSI": totalSI,
            "firePremium": round(firePremium, 2),
            "terrorismPremium": round(terrorismPremium, 2),
            "paPremium": round(paPremium, 2),
            "basePremium": round(basePremium, 2),
            "discountApplied": round(basePremium - netPremium, 2)
        }
    }

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
