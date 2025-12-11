from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func, Text, CheckConstraint, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.master import ProductMaster

class Occupancy(Base):
    __tablename__ = "occupancies"
    
    id = Column(Integer, primary_key=True, index=True)
    iib_code = Column(String(length=20), nullable=False, unique=True)
    section_aift = Column(String(length=20), nullable=False)
    occupancy_type = Column(String(length=100), nullable=False)
    occupancy_description = Column(Text, nullable=False)

class AddOnMaster(Base):
    __tablename__ = "add_on_master"
    
    id = Column(Integer, primary_key=True, index=True)
    add_on_code = Column(String(length=50), nullable=False, unique=True)
    add_on_name = Column(String(length=200), nullable=False)
    description = Column(Text, nullable=True)
    is_percentage = Column(Boolean, server_default='false', nullable=False)
    applies_to_product = Column(Boolean, server_default='true', nullable=False)
    active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AddOnProductMap(Base):
    __tablename__ = "add_on_product_map"
    
    id = Column(Integer, primary_key=True, index=True)
    add_on_id = Column(Integer, ForeignKey("add_on_master.id"), nullable=False)
    product_code = Column(String(length=50), nullable=False)
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")
    add_on = relationship("AddOnMaster")

class ProductBasicRate(Base):
    __tablename__ = "product_basic_rates"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(length=20), nullable=False)
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    occupancy_id = Column(Integer, ForeignKey("occupancies.id"), nullable=False)
    basic_rate = Column(Numeric(precision=10, scale=6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")
    occupancy = relationship("Occupancy")

class StfiRate(Base):
    __tablename__ = "stfi_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    occupancy_id = Column(Integer, ForeignKey("occupancies.id"), nullable=False, unique=True)
    product_code = Column(String(length=20), nullable=True) # Adding
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    stfi_rate = Column(Numeric(precision=10, scale=6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")
    occupancy = relationship("Occupancy")

class EqRate(Base):
    __tablename__ = "eq_rates"

    id = Column(Integer, primary_key=True, index=True)
    occupancy_id = Column(Integer, ForeignKey("occupancies.id"), nullable=False)
    product_code = Column(String(length=20), nullable=True) # Adding
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    eq_zone = Column(String(length=20), nullable=False)
    eq_rate = Column(Numeric(precision=10, scale=6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")
    occupancy = relationship("Occupancy")

class TerrorismSlab(Base):
    __tablename__ = "terrorism_slabs"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(length=20), nullable=True) # Adding
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    occupancy_type = Column(String(length=50), nullable=False)
    si_min = Column(Numeric(precision=20, scale=2), nullable=False)
    si_max = Column(Numeric(precision=20, scale=2), nullable=True)
    rate_per_mille = Column(Numeric(precision=10, scale=6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")

class BsusRate(Base):
    __tablename__ = "bsus_rates"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(length=20), nullable=True) 
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    occupancy_id = Column(Integer, ForeignKey("occupancies.id"), nullable=False)
    eq_zone = Column(String(length=20), nullable=False)
    basic_rate = Column(Numeric(precision=10, scale=6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")
    occupancy = relationship("Occupancy")

    __table_args__ = (
        UniqueConstraint('occupancy_id', 'eq_zone', name='uq_bsus_rates_occupancy_eq'),
    )

class AddOnRate(Base):
    __tablename__ = "add_on_rates"

    id = Column(Integer, primary_key=True, index=True)
    add_on_id = Column(Integer, ForeignKey("add_on_master.id"), nullable=False)
    product_code = Column(String(length=50), nullable=False)
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=True)
    occupancy_type = Column(String(length=50), nullable=True)
    si_min = Column(Numeric(precision=20, scale=2), nullable=True)
    si_max = Column(Numeric(precision=20, scale=2), nullable=True)
    rate_type = Column(String(length=30), nullable=False)
    rate_value = Column(Numeric(precision=20, scale=6), nullable=False)
    active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductMaster")
    add_on = relationship("AddOnMaster")
