"""
Pydantic schemas for Authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str


class UserPublic(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    github_username: str | None
    avatar_url: str | None
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}
