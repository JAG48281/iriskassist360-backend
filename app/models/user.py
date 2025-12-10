
from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "irisk_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    mobile = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
