
from sqlalchemy import Column, Integer, String, Float, JSON
from app.database import Base

class Rate(Base):
    __tablename__ = "irisk_rates"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True, nullable=False)
    lob = Column(String, index=True, nullable=False)
    product = Column(String, index=True, nullable=False)
    category = Column(String, nullable=True)      # e.g., occupancy
    key = Column(String, nullable=True)           # e.g., Office, Shop
    value = Column(Float, nullable=True)          # per-mille rate
    extra_metadata = Column(JSON, nullable=True)  # renamed from metadata

