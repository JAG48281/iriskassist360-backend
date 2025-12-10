
from pydantic import BaseModel
from typing import Dict, Any, Optional

class QuoteCreate(BaseModel):
    company: str
    lob: str
    product: str
    request_data: Dict[str, Any]

class QuoteOut(BaseModel):
    id: int
    user_id: Optional[int]
    company: str
    lob: str
    product: str
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]

    class Config:
        orm_mode = True
