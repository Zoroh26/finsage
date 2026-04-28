"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
import logging

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, create_access_token
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse, UserProfile, TokenResponse
from backend.app.services.auth_service import register_user, login_user, update_user_profile
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user

    - **email**: Valid email address
    - **password**: User password (will be hashed)
    - **name**: User's full name
    - **age**: User's age
    - **phone_number**: Contact number
    """
    new_user = register_user(user, db)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(user_login: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Login and get access token

    Returns JWT token in response body and sets it in HTTP-only cookie

    - **email**: User email
    - **password**: User password
    """
    db_user = login_user(user_login, db)

    # Create access token
    token = create_access_token(
        data={"sub": db_user.email, "user_id": db_user.id}
    )

    # Set cookie
    cookie_value = f"Bearer {token}"
    response.set_cookie(
        key="access_token",
        value=cookie_value,
        httponly=True,
        samesite="lax"
    )

    logger.info(
        f"Login successful for user_id={db_user.id}, email={db_user.email}")

    return TokenResponse(
        message="Logged in successfully",
        user_id=db_user.id,
        token=token
    )


@router.post("/logout")
def logout(response: Response):
    """Logout and clear access token cookie"""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile"""
    return current_user


@router.put("/users/me", response_model=UserResponse)
def update_profile(
    user_update: UserProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    updated_user = update_user_profile(current_user.id, user_update, db)
    return updated_user
