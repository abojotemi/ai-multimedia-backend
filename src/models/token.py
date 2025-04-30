from datetime import datetime
from beanie import Document
from pydantic import Field, ConfigDict
from uuid import uuid4



class BlacklistedToken(Document):
    """Model for storing blacklisted tokens"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(default_factory=lambda: str(uuid4()), alias='_id')
    token: str = Field(..., description="The blacklisted token")
    token_type: str = Field(..., description="Type of token: access or refresh")
    user_id: str = Field(..., description="ID of the user who owned the token")
    blacklisted_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(..., description="When the token expires")
    
    class Settings:
        name = "blacklisted_tokens"