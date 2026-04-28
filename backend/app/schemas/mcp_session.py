"""
MCP Session-related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional


class SessionInitRequest(BaseModel):
    """Request schema for initializing MCP session"""
    phone_number: str = Field(
        ...,
        description="Phone number linked to financial accounts"
    )


class SessionInitResponse(BaseModel):
    """Response schema for session initialization"""
    status: str
    session_id: Optional[str] = None
    message: str


class OTPVerifyRequest(BaseModel):
    """Request schema for OTP verification"""
    session_id: str
    otp: str


class SessionStatusResponse(BaseModel):
    """Response schema for session status check"""
    status: str
    message: str
