from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Otp(Base):
    __tablename__ = 'otp_codes'

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, unique=True, index=True)
    otp_code = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
