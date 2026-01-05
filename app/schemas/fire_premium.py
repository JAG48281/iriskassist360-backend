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
        populate_by_name=True,
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
    buildingSI: float = Field(0.0, ge=0, description="Building Sum Insured")
    contentsSI: float = Field(0.0, ge=0, description="Contents Sum Insured")
    terrorism_si: float = Field(0.0, description="ONLY for terrorism premium")
    
    # New specific SIs for add-on premium calculation
    lossOfRentSI: float = Field(0.0, ge=0, description="Loss of Rent Sum Insured")
    altAccommodationSI: float = Field(0.0, ge=0, description="Alternative Accommodation Sum Insured")
    valuableContentsSI: float = Field(0.0, ge=0, description="Valuable Contents Sum Insured")
    paProposerSI: float = Field(0.0, ge=0, description="PA for Proposer Sum Insured")
    paSpouseSI: float = Field(0.0, ge=0, description="PA for Spouse Sum Insured")
    
    # Optional/Alias fields for backward compatibility
    basic_cover_si: Optional[float] = Field(None, description="Alias for buildingSI")
    add_on_cover_si: Optional[float] = Field(None, description="Alias for contentsSI")
    total_sum_insured: float = Field(0, description="For reference only")
    terrorismSI: float = Field(0, description="Legacy Compat for terrorism_si")
    
    # Add-Ons
    addOns: List[AddOnItem] = Field(default_factory=list, description="Selected Add-Ons with SI")
    
    # Personal Accident
    paSelection: PASelection = Field(default_factory=PASelection, description="PA Selection")
    
    # Discount & Loading (User uses discountPercent / loadingPercent)
    discountPercentage: float = Field(default=0, ge=0, le=100, description="Discount %", alias="discountPercent")
    loadingPercentage: float = Field(default=0, ge=0, le=100, description="Loading %", alias="loadingPercent")
    
    # Policy Details
    policyPeriod: int = Field(default=1, ge=1, le=20, description="Policy Period in Years")
    
    # Risk Rate (Explicit for UBGR)
    risk_rate_per_mille: Optional[float] = Field(default=None, ge=0, description="Explicit Risk Rate (Required for UBGR)")

    @model_validator(mode='before')
    @classmethod
    def handle_si_aliases(cls, data: any) -> any:
        """Map basic_cover_si -> buildingSI and add_on_cover_si -> contentsSI and cleanse 1001_2"""
        if isinstance(data, dict):
            # 1. Alias Mapping
            if 'basic_cover_si' in data and data.get('buildingSI') is None:
                data['buildingSI'] = data['basic_cover_si']
            elif data.get('buildingSI') is None:
                data['buildingSI'] = 0.0
            
            if 'add_on_cover_si' in data and data.get('contentsSI') is None:
                data['contentsSI'] = data['add_on_cover_si']
            elif data.get('contentsSI') is None:
                data['contentsSI'] = 0.0

            if 'terrorismSI' in data and data.get('terrorism_si') is None:
                data['terrorism_si'] = data['terrorismSI']

            # Handle discountPercent / loadingPercent if passed without alias support in some contexts
            if 'discountPercent' in data and 'discountPercentage' not in data:
                data['discountPercentage'] = data['discountPercent']
            if 'loadingPercent' in data and 'loadingPercentage' not in data:
                data['loadingPercentage'] = data['loadingPercent']

            # 2. UBGR 1001_2 Cleansing
            if data.get('productCode') == "UBGR" and data.get('occupancyCode') == "1001_2":
                # Forcibly zero out add-on and PA related fields
                data['contentsSI'] = 0.0
                data['add_on_cover_si'] = 0.0
                data['lossOfRentSI'] = 0.0
                data['altAccommodationSI'] = 0.0
                data['valuableContentsSI'] = 0.0
                data['paProposerSI'] = 0.0
                data['paSpouseSI'] = 0.0
                
                # Keep ONLY TERRORISM in addOns if it exists
                current_addons = data.get('addOns', [])
                if isinstance(current_addons, list):
                    data['addOns'] = [a for a in current_addons if isinstance(a, dict) and a.get('addOnCode', '').upper() == 'TERRORISM']
                
                # Clear standard PA object if present
                if 'paSelection' in data:
                    data['paSelection'] = {"proposer": False, "spouse": False}
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
    subtotal_premium: float
    terrorism_premium: float
    discount_amount: float
    loading_amount: float
    net_premium: float
    cgst: float
    sgst: float
    stamp_duty: int = 1
    gross_premium: float
    
    # New Fields for Transparency & Validation
    total_property_si: float = 0.0
    pa_proposer_premium: float = 0.0
    pa_spouse_premium: float = 0.0
    terrorism_si: float = 0.0

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
    # Contract Fields (Mandatory)
    basic_fire_premium: float
    add_on_premium: float
    discount_amount: float
    loading_amount: float
    subtotal_premium: float
    terrorism_premium: float
    net_premium: float
    cgst: float
    sgst: float
    stamp_duty: int = 1
    gross_premium: float
    
    # New Fields for Transparency & Validation
    total_property_si: float = 0.0
    pa_proposer_premium: float = 0.0
    pa_spouse_premium: float = 0.0
    terrorism_si: float = 0.0

    # Metadata & Status (Keeping for API consistency)
    success: bool = True
    message: str = ""
    product_code: Optional[str] = Field(None, alias="productCode")
    meta: Optional[CalculationMeta] = None
    
    model_config = ConfigDict(populate_by_name=True)
