from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Quote(Base):
    __tablename__ = "irisk_quotes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("irisk_users.id"), nullable=True)
    company = Column(String)
    lob = Column(String)
    product = Column(String)
    request_data = Column(JSON)
    response_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
