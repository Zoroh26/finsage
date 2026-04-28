"""
Financial data SQLAlchemy models
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Account(Base):
    """Account database model"""
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_type = Column(String, nullable=False)
    account_number = Column(String, unique=True, nullable=False)
    institution = Column(String)

    # Relationships
    user = relationship("User", back_populates="accounts")
    holdings = relationship("Holding", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")
    epfs = relationship("EPF", back_populates="account")


class Asset(Base):
    """Asset database model"""
    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey(
        "accounts.account_id"), nullable=True)
    asset_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)

    # Relationships
    user = relationship("User", back_populates="assets")
    account = relationship("Account")
    holdings = relationship("Holding", back_populates="asset")


class Liability(Base):
    """Liability database model"""
    __tablename__ = "liabilities"

    liability_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey(
        "accounts.account_id"), nullable=True)
    liability_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)

    # Relationships
    user = relationship("User", back_populates="liabilities")
    account = relationship("Account")


class Holding(Base):
    """Holding database model"""
    __tablename__ = "holdings"

    holding_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey(
        "accounts.account_id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"), nullable=True)
    holding_type = Column(String, nullable=False)
    quantity = Column(Float)
    value = Column(Float)

    # Relationships
    account = relationship("Account", back_populates="holdings")
    asset = relationship("Asset", back_populates="holdings")


class Transaction(Base):
    """Transaction database model"""
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey(
        "accounts.account_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    transaction_type = Column(String)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    user = relationship("User")


class CreditReport(Base):
    """Credit Report database model"""
    __tablename__ = "credit_reports"

    report_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer)
    report_date = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="credit_reports")


class EPF(Base):
    """EPF (Employee Provident Fund) database model"""
    __tablename__ = "epfs"

    epf_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey(
        "accounts.account_id"), nullable=True)
    balance = Column(Float)

    # Relationships
    user = relationship("User", back_populates="epfs")
    account = relationship("Account", back_populates="epfs")


class MCPRawData(Base):
    """MCP Raw Data storage model"""
    __tablename__ = "mcp_raw_data"

    raw_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime, nullable=False)
    data = Column(JSONB, nullable=False)

    # Relationships
    user = relationship("User", back_populates="raw_data")
