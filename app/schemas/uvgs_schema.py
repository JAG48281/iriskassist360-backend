from typing import Optional
from pydantic import BaseModel, Field

class UVGSRequest(BaseModel):
    # Field definitions based on typical "Uni V... Group" policies or placeholders
    # Assuming generic inputs for now as specific fields weren't provided in the prompt
    sum_insured: float = Field(..., gt=0, description="Sum Insured Amount")
    policy_tenure: int = Field(1, ge=1, le=5, description="Tenure in years")
    member_count: int = Field(1, ge=1, description="Number of members")
    age_band: Optional[str] = Field(None, description="Age Band (e.g. 18-35)")
    
    # Add other typical fields
    coverage_type: Optional[str] = "Individual" # or Floater
