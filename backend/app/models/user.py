"""
User SQLAlchemy model
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class User(Base):
    """User database model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    age = Column(Integer)

    # Relationships
    accounts = relationship("Account", back_populates="user")
    assets = relationship("Asset", back_populates="user")
    liabilities = relationship("Liability", back_populates="user")
    credit_reports = relationship("CreditReport", back_populates="user")
    epfs = relationship("EPF", back_populates="user")
    raw_data = relationship("MCPRawData", back_populates="user")
