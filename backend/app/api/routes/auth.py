from datetime import timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter()


def _user_to_response(user: User, db: Session) -> UserResponse:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    has_profile = profile is not None and (profile.monthly_income > 0 or profile.current_savings > 0)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        has_profile=has_profile,
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    email_clean = payload.email.strip().lower()
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Password complexity check (minimum 8 characters)
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    # Hash password and create user
    hashed = hash_password(payload.password)
    user_name = payload.full_name or payload.name
    user = User(
        id=uuid.uuid4(),
        email=email_clean,
        hashed_password=hashed,
        full_name=user_name.strip() if user_name else None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token
    expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=expires)

    user_resp = _user_to_response(user, db)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_resp,
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=expires)

    user_resp = _user_to_response(user, db)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_resp,
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    return _user_to_response(current_user, db)


@router.put("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_current_user_profile(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() if payload.full_name.strip() else None
    
    if payload.password is not None:
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long.",
            )
        current_user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(current_user)
    return _user_to_response(current_user, db)
