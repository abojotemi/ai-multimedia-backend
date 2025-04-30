from enum import Enum
from multiprocessing import process
from uuid import uuid4
from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime

class Stats(Document):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    total_assets: int = Field(alias='totalAssets', default=0)
    processing: int = Field(default=0)
    storage_used: dict[str,float] = Field(alias='storageUsed', default={
        'percentage': 0,
        'used': 0,
        'total': 0
    })
    ai_insights: int = Field(alias='aiInsights', default=0)
    class Settings:
        name = "stats"

class Analytics(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    media_type_distribution: dict[str,int] = Field(alias='mediaTypeDistribution', default={
        'images': 0,
        'videos': 0,
        'audio': 0
    })
    popular_tags: list = Field(alias='popularTags', default=[])
    ai_processing_savings: dict[str, float] = Field(alias='aiProcessingSavings', default={
        'efficiency': 0,
        'timeSaved': 0
    })
    class Settings:
        name = "analytics"
