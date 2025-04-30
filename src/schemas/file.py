from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict



class AccessLevel(str, Enum):
    private = "private"
    public = "public"


class MediaResponse(BaseModel):
    id: str = Field(default_factory= lambda : str(uuid4()),alias="_id", )
    model_config = ConfigDict(populate_by_name=True)
    user_id: str
    name: str
    original_filename: str = Field(alias="originalFilename")
    file_type: str = Field(alias="fileType")
    file_size: int = Field(alias="fileSize")
    mime_type: str = Field(alias="mimeType")
    thumbnail_url: str | None = Field(default=None, alias="thumbnailUrl")
    description: str | None = None
    tags: list[str] | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    file_url: str = Field(alias="fileUrl")
    
    
class TagsUpdate(BaseModel):
    tags: list[str]