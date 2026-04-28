"""
Authentication service - User registration, login, profile management
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserLogin, UserProfile


def register_user(user: UserCreate, db: Session) -> User:
    """
    Register a new user

    Args:
        user: User registration data
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new user with hashed password
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        name=user.name,
        age=user.age,
        phone_number=user.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(user_login: UserLogin, db: Session) -> User:
    """
    Authenticate a user

    Args:
        user_login: Login credentials
        db: Database session

    Returns:
        Authenticated user object

    Raises:
        HTTPException: If credentials are invalid
    """
    db_user = db.query(User).filter(User.email == user_login.email).first()

    if not db_user or not verify_password(user_login.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return db_user


def update_user_profile(user_id: int, profile: UserProfile, db: Session) -> Optional[User]:
    """
    Update user profile information

    Args:
        user_id: ID of user to update
        profile: Profile data to update
        db: Database session

    Returns:
        Updated user object or None if not found
    """
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        return None

    # Update only provided fields
    if profile.name is not None:
        db_user.name = profile.name
    if profile.age is not None:
        db_user.age = profile.age

    db.commit()
    db.refresh(db_user)

    return db_user


def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
    """
    Get user by ID

    Args:
        user_id: User ID
        db: Database session

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(email: str, db: Session) -> Optional[User]:
    """
    Get user by email

    Args:
        email: User email
        db: Database session

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.email == email).first()
