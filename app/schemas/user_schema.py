
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    full_name: Optional[str] = None

    class Config:
        orm_mode = True
