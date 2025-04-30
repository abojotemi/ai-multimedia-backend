from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RegisterRequest(BaseModel):
    """Schema for register request"""
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Schema for token response"""
    accessToken: str = Field(..., description="JWT access token")
    refreshToken: str = Field(..., description="JWT refresh token")
    tokenType: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username",)
    email: str = Field(..., description="User email")
    created_at: str = Field(..., description="User creation timestamp")


class PasswordUpdateRequest(BaseModel):
    """Schema for password update request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token")