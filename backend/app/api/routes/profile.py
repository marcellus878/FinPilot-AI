from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.profile import (
    FinancialProfileCreate,
    FinancialProfileResponse,
    FinancialProfileUpdate,
)
from app.services.profile_service import (
    build_profile_response,
    create_or_update_user_profile,
    get_profile_by_user,
)

router = APIRouter()


@router.get("", response_model=FinancialProfileResponse, status_code=status.HTTP_200_OK)
def get_current_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialProfileResponse:
    profile = get_profile_by_user(db, current_user.id)
    if not profile:
        # Initialize default empty profile if none exists
        profile = create_or_update_user_profile(
            db,
            current_user.id,
            FinancialProfileCreate(),
        )

    return build_profile_response(profile)


@router.post("", response_model=FinancialProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_in: FinancialProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialProfileResponse:
    profile = create_or_update_user_profile(db, current_user.id, profile_in)
    return build_profile_response(profile)


@router.put("", response_model=FinancialProfileResponse, status_code=status.HTTP_200_OK)
def update_profile(
    profile_in: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialProfileResponse:
    profile = create_or_update_user_profile(db, current_user.id, profile_in)
    return build_profile_response(profile)


@router.get("/{target_user_id}", response_model=FinancialProfileResponse, status_code=status.HTTP_200_OK)
def get_user_profile_by_id(
    target_user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialProfileResponse:
    if target_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access financial profile of another user",
        )

    profile = get_profile_by_user(db, target_user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found",
        )
    return build_profile_response(profile)


@router.put("/{target_user_id}", response_model=FinancialProfileResponse, status_code=status.HTTP_200_OK)
def update_user_profile_by_id(
    target_user_id: UUID,
    profile_in: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialProfileResponse:
    if target_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot update financial profile of another user",
        )

    profile = create_or_update_user_profile(db, target_user_id, profile_in)
    return build_profile_response(profile)
