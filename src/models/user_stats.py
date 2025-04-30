from uuid import uuid4
from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime

class UserStats(Document):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(required=True, alias='userId')
    total_assets: int = Field(alias='totalAssets', default=0)
    total_storage_used: float = Field(alias='totalStorageUsed', default=0)  # in MB
    recent_media: list[str] = Field(alias='recentMedia', default=[])  # list of media IDs
    upload_count: int = Field(alias='uploadCount', default=0)
    last_upload_date: datetime = Field(alias='lastUploadDate', default_factory=datetime.now)
    media_type_counts: dict[str, int] = Field(alias='mediaTypeCounts', default={
        'image': 0,
        'video': 0,
        'audio': 0,
        'document': 0
    })
    tags: set[str] = Field(default=set())
    created_at: datetime = Field(default_factory=datetime.now, alias='createdAt')
    updated_at: datetime = Field(default_factory=datetime.now, alias='updatedAt')
    
    class Settings:
        name = "user_stats" 
        
    async def update_on_deletion(self, media_id: str, file_size_mb: float, media_type: str) -> None:
        """
        Update user stats when a media item is deleted
        
        Args:
            media_id: ID of the deleted media
            file_size_mb: Size of the deleted file in MB
            media_type: Type of the deleted media (image, video, audio, document)
        """
        # Decrease total storage used
        self.total_storage_used = max(0, self.total_storage_used - file_size_mb)
        
        # Decrease total assets
        self.total_assets = max(0, self.total_assets - 1)
        
        # Update media type count
        if media_type in self.media_type_counts:
            self.media_type_counts[media_type] = max(0, self.media_type_counts[media_type] - 1)
            
        # Remove from recent media if present
        if media_id in self.recent_media:
            self.recent_media.remove(media_id)
            
        # Update timestamp
        self.updated_at = datetime.now()
        
        # Save changes
        await self.save()