from datetime import datetime
from beanie import Document
from pydantic import ConfigDict, Field
from uuid import uuid4


class User(Document):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(default_factory=lambda: str(uuid4()), alias='_id')
    username: str = Field(required=True, unique=True)
    email: str = Field(required=True, unique=True)
    password_hash: str = Field(required=True, exclue=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    class Settings:
        name = "users"
