from pydantic import BaseModel, Field
from typing import List, Optional

class RatingRequest(BaseModel):
    product_name: str
    sum_insured: float = Field(..., gt=0)
    rate: float = Field(..., gt=0)
    discounts_pct: List[float] = []
    loadings_pct: List[float] = []
    
class RatingResponse(BaseModel):
    base_premium: float
    net_premium: float
    cgst: float
    sgst: float
    igst: float
    total_premium: float
    breakdown: dict
