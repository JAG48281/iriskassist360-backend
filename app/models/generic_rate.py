from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, JSON, UniqueConstraint, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class GenericRateTable(Base):
    __tablename__ = "generic_rate_tables"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=False)
    rate_key = Column(String, nullable=False)
    rate_value = Column(Numeric, nullable=False)
    rate_type = Column(String, nullable=False) # percentage, per_mille, flat, amount
    conditions = Column(JSON, nullable=True)
    si_min = Column(Numeric, nullable=True)
    si_max = Column(Numeric, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("app.models.master.ProductMaster")

    __table_args__ = (
        UniqueConstraint('product_id', 'rate_key', 'si_min', 'si_max', name='uq_generic_rate_product_key_si'),
    )
