from uuid import uuid4
from beanie import Document
from pydantic import Field, BaseModel, ConfigDict
from datetime import datetime
from src.utils.types import FileType


class Metadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(required=True, alias='userId')
    name: str | None = None
    tags: list[str] = []
    date: datetime = Field(default_factory=datetime.now)
    assets: int = Field(default=0, ge=0)
    
    class Settings:
        name = "metadata"
