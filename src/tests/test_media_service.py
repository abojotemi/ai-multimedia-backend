import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.models.media_item import MediaItem
from src.models.user import User
from src.models.user_stats import UserStats
from src.service.media import MediaService


@pytest.fixture
def media_service():
    return MediaService()


@pytest.fixture
def mock_user():
    return User(
        id="user123",
        username="testuser",
        email="test@example.com",
        password="hashedpassword",
    )


@pytest.fixture
def mock_media_item():
    return MediaItem(
        id="media123",
        user_id="user123",
        name="Test Media",
        original_filename="test.jpg",
        file_type="image",
        mime_type="image/jpeg",
        file_size=1024 * 1024,  # 1MB
        file_url="http://example.com/test.jpg",
        tags=["nature", "landscape", "mountain"],
    )


@pytest.fixture
def mock_user_stats():
    return UserStats(
        id="stats123",
        user_id="user123",
        total_assets=5,
        total_storage_used=5.0,
        recent_media=["media456", "media789"],
        upload_count=5,
        last_upload_date=datetime.now(),
        media_type_counts={"image": 3, "video": 2},
        tags={"portrait", "sunset"},
    )


@pytest.mark.asyncio
async def test_update_user_stats_with_tags(media_service, mock_media_item, mock_user_stats):
    # Mock the UserStats.find_one method
    with patch("src.models.user_stats.UserStats.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = mock_user_stats
        
        # Mock the save method
        mock_user_stats.save = AsyncMock()
        
        # Call the method
        await media_service.update_user_stats(mock_media_item, "user123")
        
        # Verify that find_one was called with the correct parameters
        mock_find_one.assert_called_once()
        
        # Verify that the user stats were updated correctly
        assert mock_user_stats.total_assets == 6
        assert mock_user_stats.upload_count == 6
        assert mock_user_stats.media_type_counts["image"] == 4
        
        # Verify that the tags were updated correctly
        expected_tags = {"portrait", "sunset", "nature", "landscape", "mountain"}
        assert mock_user_stats.tags == expected_tags
        
        # Verify that save was called
        mock_user_stats.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_stats_new_user(media_service, mock_media_item):
    # Mock the UserStats.find_one method to return None (new user)
    with patch("src.models.user_stats.UserStats.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = None
        
        # Mock the UserStats.create method
        with patch("src.models.user_stats.UserStats.save", new_callable=AsyncMock) as mock_save:
            # Call the method
            await media_service.update_user_stats(mock_media_item, "user123")
            
            # Verify that find_one was called with the correct parameters
            mock_find_one.assert_called_once()
            
            # Verify that save was called
            mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_update_media_tags(media_service, mock_media_item, mock_user_stats):
    # Mock the MediaItem.find_one method
    with patch("src.models.media_item.MediaItem.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = mock_media_item
        
        # Mock the save method
        mock_media_item.save = AsyncMock()
        
        # Mock the update_user_tags method
        with patch.object(media_service, "update_user_tags", new_callable=AsyncMock) as mock_update_user_tags:
            # Call the method
            new_tags = ["sunset", "beach", "vacation"]
            result = await media_service.update_media_tags("media123", new_tags, "user123")
            
            # Verify that find_one was called with the correct parameters
            mock_find_one.assert_called_once()
            
            # Verify that the media item tags were updated correctly
            assert result.tags == new_tags
            
            # Verify that save was called
            mock_media_item.save.assert_called_once()
            
            # Verify that update_user_tags was called
            mock_update_user_tags.assert_called_once_with("user123")


@pytest.mark.asyncio
async def test_update_user_tags(media_service, mock_user_stats):
    # Create mock media items with different tags
    media_items = [
        MediaItem(id="media1", user_id="user123", name="Media 1", original_filename="file1.jpg", tags=["nature", "landscape"]),
        MediaItem(id="media2", user_id="user123", name="Media 2", original_filename="file2.jpg", tags=["portrait", "people"]),
        MediaItem(id="media3", user_id="user123", name="Media 3", original_filename="file3.jpg", tags=["landscape", "sunset"])
    ]
    
    # Mock the MediaItem.find method
    with patch("src.models.media_item.MediaItem.find") as mock_find:
        mock_find_cursor = AsyncMock()
        mock_find_cursor.to_list = AsyncMock(return_value=media_items)
        mock_find.return_value = mock_find_cursor
        
        # Mock the UserStats.find_one method
        with patch("src.models.user_stats.UserStats.find_one", new_callable=AsyncMock) as mock_find_one:
            mock_find_one.return_value = mock_user_stats
            
            # Mock the save method
            mock_user_stats.save = AsyncMock()
            
            # Call the method
            result = await media_service.update_user_tags("user123")
            
            # Verify that find was called with the correct parameters
            mock_find.assert_called_once()
            
            # Verify that the user stats tags were updated correctly
            expected_tags = {"nature", "landscape", "portrait", "people", "sunset"}
            assert mock_user_stats.tags == expected_tags
            assert result == expected_tags
            
            # Verify that save was called
            mock_user_stats.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_all_users_tags(media_service):
    # Create mock media items with different user IDs and tags
    media_items = [
        MediaItem(id="media1", user_id="user1", name="Media 1", original_filename="file1.jpg", tags=["nature", "landscape"]),
        MediaItem(id="media2", user_id="user1", name="Media 2", original_filename="file2.jpg", tags=["portrait", "people"]),
        MediaItem(id="media3", user_id="user2", name="Media 3", original_filename="file3.jpg", tags=["landscape", "sunset"]),
        MediaItem(id="media4", user_id="user2", name="Media 4", original_filename="file4.jpg", tags=["city", "architecture"])
    ]
    
    # Mock the MediaItem.find_all method
    with patch("src.models.media_item.MediaItem.find_all") as mock_find_all:
        mock_find_cursor = AsyncMock()
        mock_find_cursor.to_list = AsyncMock(return_value=media_items)
        mock_find_all.return_value = mock_find_cursor
        
        # Mock the update_user_tags method
        with patch.object(media_service, "update_user_tags", new_callable=AsyncMock) as mock_update_user_tags:
            # Set up return values for update_user_tags
            mock_update_user_tags.side_effect = [
                {"nature", "landscape", "portrait", "people"},  # user1
                {"landscape", "sunset", "city", "architecture"}  # user2
            ]
            
            # Call the method
            result = await media_service.update_all_users_tags()
            
            # Verify that find_all was called
            mock_find_all.assert_called_once()
            
            # Verify that update_user_tags was called for each user
            assert mock_update_user_tags.call_count == 2
            mock_update_user_tags.assert_any_call("user1")
            mock_update_user_tags.assert_any_call("user2")
            
            # Verify the results
            expected_results = {
                "user1": ["nature", "landscape", "portrait", "people"],
                "user2": ["landscape", "sunset", "city", "architecture"]
            }
            # Since sets are converted to lists, the order might be different
            assert set(result["user1"]) == set(expected_results["user1"])
            assert set(result["user2"]) == set(expected_results["user2"])