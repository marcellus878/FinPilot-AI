from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: Optional[str] = Field(None, max_length=255, description="Full name of user")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of user")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    has_profile: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
