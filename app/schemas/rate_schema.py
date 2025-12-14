
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class RateCreate(BaseModel):
    company: str
    lob: str
    product: str
    category: Optional[str]
    key: Optional[str]
    value: Optional[float]
    metadata: Optional[Dict[str, Any]] = None

class RateOut(RateCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int

