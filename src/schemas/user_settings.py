from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UserProfileUpdate(BaseModel):
    """Schema for user profile update"""
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="User email")
    display_name: Optional[str] = Field(None, description="Display name")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


class UserPasswordUpdate(BaseModel):
    """Schema for user password update"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")


class UserSettings(BaseModel):
    """Schema for user settings"""
    theme: str = Field(default="light", description="UI theme")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    default_privacy: str = Field(default="private", description="Default privacy setting")
    ai_processing_enabled: bool = Field(default=True, description="Enable AI processing")
    display_preferences: Dict[str, Any] = Field(default_factory=dict, description="Display preferences")


class UserSettingsResponse(BaseModel):
    """Schema for user settings response"""
    id: str = Field(..., description="User ID")
    settings: UserSettings = Field(..., description="User settings")