from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field, ConfigDict

# from uuid import uuid4
from src.models.folder import User, Folder
from src.utils.types import FileType, ProcessType


class ActivityLog(Document):
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: User = Field(required=True, alias="userId")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.now, alias="updatedAt")

    class Settings:
        name = "media_item"
        # indexes = [
        #     [("user_id", 1), ("name", 1), {"unique": True}]  # Compound unique index
        # ]



class AiResult(BaseModel):
    tags: list[str]
    transcription: str
    ocrText: str
    objects: list[str]
    moderation: dict
