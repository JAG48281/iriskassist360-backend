from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class LobMaster(Base):
    __tablename__ = "lob_master"

    id = Column(Integer, primary_key=True, index=True)
    lob_code = Column(String, unique=True, index=True, nullable=False)
    lob_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)

    products = relationship("ProductMaster", back_populates="lob")

class ProductMaster(Base):
    __tablename__ = "product_master"

    id = Column(Integer, primary_key=True, index=True)
    lob_id = Column(Integer, ForeignKey("lob_master.id"), nullable=False)
    product_code = Column(String, index=True, nullable=False)
    product_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)

    lob = relationship("LobMaster", back_populates="products")

    __table_args__ = (
        UniqueConstraint('lob_id', 'product_code', name='uq_product_master_lob_product'),
    )
