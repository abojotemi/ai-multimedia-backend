from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field, ConfigDict
from src.utils.types import FileType, ProcessType
from uuid import uuid4


class MediaItem(Document):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid4()), alias='_id')
    user_id: str = Field(required=True, alias='userId')
    name: str = Field(required=True)
    description: str | None = Field(default=None)
    original_filename: str = Field(required=True, alias='originalFilename')
    file_type: FileType = Field(default="unknown", alias='fileType')
    mime_type: str = Field(default="unknown", alias='mimeType')
    file_size: int = Field(default=0, alias='fileSize')
    file_url: str = Field(default=None, alias='fileUrl')
    processing_status: ProcessType = Field(default="pending", alias='processingStatus')
    requested_ai_options: dict[str, bool] = Field(default={}, alias='requestedAiOptions')
    tags: list[str] = Field(default=[], alias='tags')
    error_message: str | None = Field(default=None, alias='errorMessage')
    thumbnail_url: str | None = Field(default=None, alias='thumbnailUrl')
    width: int  = Field(default=0)
    height: int = Field(default=0)
    duration: float = Field(default=0.0, alias='durationSeconds')
    created_at: datetime = Field(default_factory=datetime.now, alias='createdAt')
    updated_at: datetime = Field(default_factory=datetime.now, alias='updatedAt')

    class Settings:
        name = "media_item"




class AiResult(BaseModel):
    tags: list[str]
    transcription: str
    ocrText: str
    objects: list[str]
    moderation: dict