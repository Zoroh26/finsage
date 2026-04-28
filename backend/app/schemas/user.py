"""
User-related Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: Optional[str] = None
    age: Optional[int] = None


class UserCreate(UserBase):
    """Schema for user registration"""
    phone_number: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for login response"""
    message: str
    user_id: int
    token: str
