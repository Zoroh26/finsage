"""
Security utilities - JWT, password hashing, authentication
"""
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
import logging

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.user import User

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({'exp': expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        logger.debug(f"Token decoded successfully. Payload: {payload}")

        if "user_id" not in payload:
            logger.error("Token payload missing user_id field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )

        return payload

    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT decode error: {str(e)}"
        )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Get the current authenticated user from request

    Supports both:
    - Cookie-based auth (access_token cookie)
    - Header-based auth (Authorization: Bearer <token>)

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = None

    # Try to get token from cookie first
    cookie_value = request.cookies.get("access_token")
    if cookie_value:
        logger.debug(f"Found access_token cookie: {cookie_value[:50]}...")
        if cookie_value.startswith("Bearer "):
            token = cookie_value.split(" ")[1]
        else:
            token = cookie_value

    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.debug("Using token from Authorization header")

    if not token:
        logger.error("No access_token cookie or Authorization header found")
        logger.debug(f"Available cookies: {list(request.cookies.keys())}")
        logger.debug(f"Headers: {dict(request.headers)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify token
    payload = verify_token(token)
    user_id = payload.get("user_id")

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User not found for user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    logger.debug(f"Authenticated user: {user.email} (id={user.id})")
    return user
