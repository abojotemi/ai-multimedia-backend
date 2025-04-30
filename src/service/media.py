# from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.models.media_item import MediaItem
from src.models.user import User
from src.models.user_stats import UserStats
from src.schemas.file import MediaResponse
from src.utils import auth
import random
from datetime import datetime, timedelta


class MediaService:
    async def add_media(self, media: MediaResponse, user: User):
        data = media.model_dump()
        media_item = MediaItem(**data)
        await media_item.create()

        # Update user statistics
        await self.update_user_stats(media_item, user.id)

    async def update_user_stats(self, media_item: MediaItem, user_id: str):
        """Update user statistics after adding new media"""
        # Find existing user stats or create new
        user_stats = await UserStats.find_one(UserStats.user_id == user_id)

        if not user_stats:
            user_stats = UserStats(userId=user_id)

        # Update statistics
        user_stats.total_assets += 1
        user_stats.total_storage_used += media_item.file_size / (
            1024 * 1024
        )  # Convert to MB
        user_stats.upload_count += 1
        user_stats.last_upload_date = datetime.now()

        # Increment the appropriate media type count
        media_type = media_item.file_type.lower()
        user_stats.media_type_counts[media_type] = (
            user_stats.media_type_counts.get(media_type, 0) + 1
        )

        # Update recent media (keep the 5 most recent)
        if media_item.id not in user_stats.recent_media:
            user_stats.recent_media.insert(0, media_item.id)
            user_stats.recent_media = user_stats.recent_media[
                :5
            ]  # Keep only 5 most recent
            
        # Update user's tags with all tags from the media item
        if media_item.tags:
            # Convert the set to a list, add new tags, and convert back to a set
            current_tags = set(user_stats.tags)
            current_tags.update(media_item.tags)
            user_stats.tags = current_tags

        user_stats.updated_at = datetime.now()
        await user_stats.save()

    async def update_media_tags(self, media_id: str, tags: list[str], user_id: str):
        """Update tags for a media item and update user stats accordingly"""
        # Find the media item
        media_item = await MediaItem.find_one(MediaItem.id == media_id, MediaItem.user_id == user_id)
        
        if not media_item:
            return None
            
        # Update the media item tags
        media_item.tags = tags
        media_item.updated_at = datetime.now()
        await media_item.save()
        
        # Update user stats with all tags from all media items
        await self.update_user_tags(user_id)
        
        return media_item
        
    async def update_user_tags(self, user_id: str):
        """Update user stats with all tags from all media items"""
        # Find all media items for the user
        media_items = await MediaItem.find(MediaItem.user_id == user_id).to_list()
        
        # Collect all unique tags
        all_tags = set()
        for item in media_items:
            if item.tags:
                all_tags.update(item.tags)
                
        # Update user stats
        user_stats = await UserStats.find_one(UserStats.user_id == user_id)
        if user_stats:
            user_stats.tags = all_tags
            user_stats.updated_at = datetime.now()
            await user_stats.save()
            
        return all_tags
        
    async def get_media(self, type: str, user: User):
        # Check if there are any media items for this user
        print(MediaItem.user_id, user.id)
        if type == 'all':
            items = await MediaItem.find(MediaItem.user_id == user.id).to_list()
        else:
            items = await MediaItem.find(
                MediaItem.user_id == user.id, MediaItem.file_type == type
            ).to_list()
        return items
        
    async def delete_media(self, media_id: str, user_id: str):
        """Delete a media item and update user statistics"""
        # Find the media item
        media_item = await MediaItem.find_one(MediaItem.id == media_id and MediaItem.user_id == user_id)
        if not media_item:
            return None
            
        # Store properties needed for stats update
        file_size = media_item.file_size
        file_type = media_item.file_type
        
        # Delete the media item
        await media_item.delete()
        
        # Update user statistics
        user_stats = await UserStats.find_one(UserStats.user_id == user_id)
        
        if user_stats:
            # Decrement counts
            user_stats.total_assets = max(0, user_stats.total_assets - 1)
            user_stats.total_storage_used = max(0, user_stats.total_storage_used - (file_size / (1024 * 1024)))  # Convert to MB
            
            # Decrement the appropriate media type count
            media_type = file_type.lower()
            if media_type in user_stats.media_type_counts:
                user_stats.media_type_counts[media_type] = max(0, user_stats.media_type_counts.get(media_type, 0) - 1)
            
            # Remove from recent media if present
            if media_id in user_stats.recent_media:
                user_stats.recent_media.remove(media_id)
            
            # Update tags (optional - could be expensive for users with many media items)
            await self.update_user_tags(user_id)
            
            user_stats.updated_at = datetime.now()
            await user_stats.save()
        
        return {"success": True, "message": "Media item deleted successfully"}

    async def update_all_users_tags(self):
        """Update tags for all users based on their media items"""
        # Find all users
        users = await User.find_all().to_list()
        results = []
        
        for user in users:
            tags = await self.update_user_tags(user.id)
            results.append({"user_id": user.id, "tag_count": len(tags)})
            
        return results


media_service = MediaService()
