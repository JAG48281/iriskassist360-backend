
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    full_name: Optional[str] = None

