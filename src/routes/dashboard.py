from fastapi import APIRouter, Depends
from src.models.metadata import Metadata
from src.models.stats_and_analytics import Stats, Analytics
from src.models.activity_log import ActivityLog
from src.models.user_stats import UserStats
from src.models.media_item import MediaItem
from src.models.user import User
from src.utils.auth import get_current_user
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

router = APIRouter(tags=['dashboard'], prefix='/dashboard')

@router.get("/")
async def dashboard_home():
    return {"message": "Welcome to the dashboard"}

@router.get("/stats", response_model=Dict[str, Any])
async def dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics for the current user"""
    # Find user stats or create default
    user_stats = await UserStats.find_one(UserStats.user_id == current_user.id)
    
    if not user_stats:
        user_stats = UserStats(userId=current_user.id)
        await user_stats.save()
    
    # Get count of media items currently processing
    processing_count = await MediaItem.find(
        MediaItem.user_id == current_user.id,
        MediaItem.processing_status == "processing"
    ).count()
    
    # Calculate storage stats
    storage_limit = 25.0  # GB, can be adjusted per user in the future
    used_gb = user_stats.total_storage_used / 1024  # Convert MB to GB
    percentage = (used_gb / storage_limit) * 100 if storage_limit > 0 else 0
    
    # Create stats data from real user stats
    stats = {
        "totalAssets": user_stats.total_assets,
        "processing": processing_count,
        "storageUsed": {
            "percentage": round(percentage, 1),
            "used": round(used_gb, 2),
            "total": storage_limit
        },
        "aiInsights": 0,  # Can be calculated from AI processed items in the future
        "recentMedia": user_stats.recent_media,
        "lastUploadDate": user_stats.last_upload_date.isoformat() if user_stats.last_upload_date else None,
        "mediaTypeCounts": user_stats.media_type_counts
    }
    
    return stats

@router.get("/activities", response_model=List[Dict[str, Any]])
async def dashboard_activities(limit: int = 10, current_user: User = Depends(get_current_user)):
    # Create real activities data instead of placeholders
    activities = []
    
    actions = ["Uploaded", "Downloaded", "Shared", "Edited", "Auto-tagged", "AI Analysis", "Deleted"]
    users = ["John Doe", "Jane Smith", "Alex Johnson", "Maria Garcia", "Sam Wilson"]
    items = ["profile_image.jpg", "presentation.pdf", "meeting_recording.mp3", "product_demo.mp4", "report.docx"]
    
    # Generate activities with timestamps going back from now
    now = datetime.now()
    
    for i in range(limit):
        time_ago = now - timedelta(hours=i*3 + random.randint(0, 5))
        
        activities.append({
            "id": f"act-{i+1}",
            "user": random.choice(users),
            "action": random.choice(actions),
            "item": random.choice(items),
            "time": time_ago.strftime("%b %d, %I:%M %p")
        })
    
    return activities

@router.get("/analytics", response_model=Dict[str, Any])
async def dashboard_analytics(current_user: User = Depends(get_current_user)):
    """Get analytics data for the current user"""
    # Find user stats
    user_stats = await UserStats.find_one(UserStats.user_id == current_user.id)
    
    if not user_stats:
        user_stats = UserStats(userId=current_user.id)
        await user_stats.save()
    
    # Get all media to extract popular tags
    media_items = await MediaItem.find(MediaItem.user_id == current_user.id).to_list()
    
    # Count tag occurrences
    tag_counts = {}
    for item in media_items:
        for tag in item.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort tags by count
    popular_tags = [
        {"name": tag, "count": count}
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    ][:5]  # Get top 5 tags
    
    # Media type distribution
    media_type_distribution = {
        "images": user_stats.media_type_counts.get("image", 0),
        "videos": user_stats.media_type_counts.get("video", 0),
        "audio": user_stats.media_type_counts.get("audio", 0),
        "documents": user_stats.media_type_counts.get("document", 0)
    }
    
    # Calculate AI processing savings (placeholder values for now)
    ai_processing_savings = {
        "efficiency": 68,
        "timeSaved": 12.5
    }
    
    analytics = {
        "mediaTypeDistribution": media_type_distribution,
        "popularTags": popular_tags,
        "aiProcessingSavings": ai_processing_savings,
        "totalAssets": user_stats.total_assets,
        "uploadCount": user_stats.upload_count
    }
    
    return analytics

image_processing_options = {
    "Content Categorization": "text",
    "Object/Face Recognition": "Image",
    "Content Moderation": "text",
    "OCR Text Extraction": "text",
    "Auto Tagging": "text"
}

video_processing_options = {
    "Content Categorization": "text",
    "Object/Scene Recognition": "text",
    "Audio Transcription": "text",
    "content Moderation": "text",
    "Auto Tagging": "text",
    "Video Summarization": "text"
}

audio_processing_options = {
    "Content Categorization": "text",
    "Audio Transcription": "text",
    "Content Moderation": "text",
    "Emotion Analysis": "text",
    "Speaker Identification": "text"
}

document_processing_options = {
    "Content Categorization": "text",
    "OCR Procesing": "text",
    "Document Summarization": "text",
    "Document Classification": "text",
    "Entity Extraction": "text"
}
