from beanie import Document
from pydantic import ConfigDict, Field
from typing import Dict, Any
from uuid import uuid4


class UserSettings(Document):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(default_factory=lambda: str(uuid4()), alias='_id')
    user_id: str = Field(..., description="User ID")
    theme: str = Field(default="light", description="UI theme")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    default_privacy: str = Field(default="private", description="Default privacy setting")
    ai_processing_enabled: bool = Field(default=True, description="Enable AI processing")
    display_preferences: Dict[str, Any] = Field(default_factory=dict, description="Display preferences")
    
    class Settings:
        name = "user_settings"