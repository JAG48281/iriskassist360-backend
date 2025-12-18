from pydantic import BaseModel, Field, ConfigDict
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
    model_config = ConfigDict(
        json_schema_extra={
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
    )
    
    productCode: str = Field(..., description="UBGR or UVGR")
    occupancyCode: str = Field(..., description="IIB Code (e.g., 1001, 1001_2)")
    
    # Sum Insured Components
    buildingSI: float = Field(..., ge=0, description="Building Sum Insured")
    contentsSI: float = Field(default=0, ge=0, description="Contents Sum Insured")
    terrorismSI: float = Field(default=0, ge=0, description="Terrorism Sum Insured (Mandatory for Terrorism calc)")
    
    # Add-Ons
    addOns: List[AddOnItem] = Field(default_factory=list, description="Selected Add-Ons with SI")
    
    # Personal Accident
    paSelection: PASelection = Field(default_factory=PASelection, description="PA Selection")
    
    # Discount & Loading
    discountPercentage: float = Field(default=0, ge=0, le=100, description="Discount %")
    loadingPercentage: float = Field(default=0, ge=0, le=100, description="Loading %")
    
    # Policy Details
    policyPeriod: int = Field(default=1, ge=1, le=20, description="Policy Period in Years")
    
    # Risk Rate (Explicit for UBGR)
    risk_rate_per_mille: Optional[float] = Field(default=None, ge=0, description="Explicit Risk Rate (Required for UBGR)")


class PremiumBreakdown(BaseModel):
    """Detailed breakdown of premium calculation - Monetary Values ONLY"""
    basic_premium: float
    add_on_premium: float
    discount_amount: float
    sub_total: float
    loading_amount: float
    terrorism_premium: Optional[float] = None
    annual_net_premium: float  # 1-year net premium before policy period multiplier
    net_premium: float  # Multi-year net (annual_net × policy_period_years)
    cgst: float
    sgst: float
    stamp_duty: float
    gross_premium: float

class CalculationMeta(BaseModel):
    """Metadata for transparency"""
    applied_rate: float  # Basic fire rate per mille
    risk_rate: float  # Same as applied_rate (for clarity in UI)
    rate_source: str = "product_basic_rates"  # Source of the rate
    terrorism_rate: Optional[float] = None
    occupancy_code: str
    product_code: str
    policy_period_years: int  # Policy period used in calculation


class UBGRUVGRResponse(BaseModel):
    """Response schema for UBGR/UVGR premium calculation"""
    success: bool
    message: str
    product_code: str = Field(..., alias="productCode") # Alias to maintain backward compat if needed? User said clean. I'll stick to snake_case if user didn't specify. 
    # User requirement: "Return a structured JSON... Expose ONLY the canonical snake_case fields".
    # User also listed "product_code" in meta.
    # The top level response has `productCode` in camelCase in the previous file.
    # The user mandated: "Expose ONLY the canonical snake_case fields" - this likely applies to the breakdown mostly.
    # But "productCode" vs "product_code" in root?
    # I'll use `product_code` in root to be safe, but alias it if I fear breaking frontend immediate.
    # The user said "Ensure frontend needs ZERO interpretation". Snake case is usually preferred in Python backends but camelCase in JS.
    # Whatever I choose, I must be consistent. The prompt explicitly used snake_case in the JSON example: `{ basic_premium, ... }`.
    # I will use snake_case for everything.
    
    breakdown: PremiumBreakdown
    meta: CalculationMeta
