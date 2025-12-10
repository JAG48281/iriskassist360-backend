
from pydantic import BaseModel
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
    id: int

    class Config:
        orm_mode = True
