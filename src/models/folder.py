from datetime import datetime
from beanie import Document
from pydantic import Field
from uuid import uuid4
from src.models.user import User


class Folder(Document):
    id: str = Field(default_factory=lambda: str(uuid4()), alias='_id')
    user_id: User = Field(required=True, alias='userId')
    name: str = Field(required=True)
    created_at: datetime = Field(default_factory=datetime.now, alias='createdAt')
    updated_at: datetime = Field(default_factory=datetime.now, alias='updatedAt')
    
    class Settings:
        name = "folder"
        # indexes = [
        #     [("user_id", 1), ("name", 1), {"unique": True}]  # Compound unique index
        # ]
