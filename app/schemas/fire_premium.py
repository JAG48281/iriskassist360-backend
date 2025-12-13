from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from decimal import Decimal

class AddOnItem(BaseModel):
    """Individual Add-On with SI"""
    addOnCode: str = Field(..., description="Add-on code from master")
    sumInsured: float = Field(..., ge=0, description="Sum Insured for this add-on")

class PASelection(BaseModel):
    """Personal Accident Selection"""
    proposer: bool = Field(default=False, description="PA for Proposer")
    spouse: bool = Field(default=False, description="PA for Spouse")

class UBGRUVGRRequest(BaseModel):
    """
    Request schema for UBGR/UVGR premium calculation.
    Supports both products with identical calculation logic.
    """
    productCode: str = Field(..., description="UBGR or UVGR")
    occupancyCode: str = Field(..., description="IIB Code (e.g., 1001, 1001_2)")
    
    # Sum Insured Components
    buildingSI: float = Field(..., ge=0, description="Building Sum Insured")
    contentsSI: float = Field(default=0, ge=0, description="Contents Sum Insured")
    
    # Add-Ons
    addOns: List[AddOnItem] = Field(default_factory=list, description="Selected Add-Ons with SI")
    
    # Personal Accident
    paSelection: PASelection = Field(default_factory=PASelection, description="PA Selection")
    
    # Discount & Loading
    discountPercentage: float = Field(default=0, ge=0, le=100, description="Discount %")
    loadingPercentage: float = Field(default=0, ge=0, le=100, description="Loading %")
    
    class Config:
        schema_extra = {
            "example": {
                "productCode": "UBGR",
                "occupancyCode": "1001",
                "buildingSI": 1000000,
                "contentsSI": 200000,
                "addOns": [
                    {"addOnCode": "EQ", "sumInsured": 1200000}
                ],
                "paSelection": {"proposer": True, "spouse": False},
                "discountPercentage": 5,
                "loadingPercentage": 10
            }
        }

class PremiumBreakdown(BaseModel):
    """Detailed breakdown of premium calculation"""
    basicFirePremium: float
    addOnPremium: float
    discountAmount: float
    subtotal: float
    loadingAmount: float
    terrorismPremium: Optional[float]
    netPremium: float
    cgst: float
    sgst: float
    stampDuty: float
    grossPremium: float
    
    # Additional details for transparency
    totalSI: float
    basicFireRate: float
    terrorismRate: Optional[float]
    addOnDetails: List[Dict] = Field(default_factory=list)
    
class UBGRUVGRResponse(BaseModel):
    """Response schema for UBGR/UVGR premium calculation"""
    success: bool
    message: str
    productCode: str
    breakdown: PremiumBreakdown
