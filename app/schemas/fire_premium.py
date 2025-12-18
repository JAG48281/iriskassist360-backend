from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
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
    
    # Primary fields for UBGR/BGRP
    buildingSI: float = Field(..., ge=0, description="Building Sum Insured")
    contentsSI: float = Field(..., ge=0, description="Contents Sum Insured")
    terrorism_si: float = Field(0, description="ONLY for terrorism premium")
    
    # Optional/Alias fields for backward compatibility
    basic_cover_si: Optional[float] = Field(None, description="Alias for buildingSI")
    add_on_cover_si: Optional[float] = Field(None, description="Alias for contentsSI")
    total_sum_insured: float = Field(0, description="For reference only")
    terrorismSI: float = Field(0, description="Legacy Compat for terrorism_si")
    
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

    @model_validator(mode='before')
    @classmethod
    def handle_si_aliases(cls, data: any) -> any:
        """Map basic_cover_si -> buildingSI and add_on_cover_si -> contentsSI"""
        if isinstance(data, dict):
            # Map basic_cover_si to buildingSI if buildingSI is not provided
            if 'basic_cover_si' in data and data.get('buildingSI') is None:
                data['buildingSI'] = data['basic_cover_si']
            elif data.get('buildingSI') is None:
                data['buildingSI'] = 0.0
            
            # Map add_on_cover_si to contentsSI if contentsSI is not provided
            if 'add_on_cover_si' in data and data.get('contentsSI') is None:
                data['contentsSI'] = data['add_on_cover_si']
            elif data.get('contentsSI') is None:
                data['contentsSI'] = 0.0

            # terrorism_si mapping
            if 'terrorismSI' in data and data.get('terrorism_si') is None:
                data['terrorism_si'] = data['terrorismSI']
        return data

    @field_validator('policyPeriod', mode='before')
    @classmethod
    def parse_policy_period(cls, v):
        """Parse policy period from string format like '2 Years' or integer"""
        if isinstance(v, str):
            import re
            match = re.search(r'(\d+)', v)
            if match:
                return int(match.group(1))
            return 1
        return v

class PremiumBreakdown(BaseModel):
    """Detailed breakdown of premium calculation - Monetary Values ONLY"""
    basic_fire_premium: float
    add_on_premium: float
    subtotal: float
    terrorism_premium: float
    discount_amount: float
    loading_amount: float
    net_premium: float
    cgst: float
    sgst: float
    stamp_duty: float = 1.0
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
    optional_addons_applicable: bool = True


class UBGRUVGRResponse(BaseModel):
    """Response schema for UBGR/UVGR premium calculation"""
    success: bool
    message: str
    product_code: str = Field(..., alias="productCode")
    optional_addons_applicable: bool = True
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
