import asyncio
from fastapi import APIRouter, File, UploadFile
from datetime import datetime
from src.models.user_stats import UserStats
from src.utils.auth import get_current_user
from src.ai.pyd_ai import tag_files
from src.models.media_item import MediaItem
from src.schemas.ai import AIResponse
from src.schemas.file import MediaResponse, TagsUpdate
from src.service.media import media_service
from src.utils.cloudinary_script import upload_file
from src.models.user import User
import os
from uuid import uuid4
from fastapi import Depends, HTTPException

router = APIRouter(prefix="/media", tags=["Media"])

responses = []


@router.post("/upload", response_model=list[MediaItem])
async def upload_files(
    files: list[UploadFile] = File(...),
    # access_level: AccessLevel = Form(...)
    user: User = Depends(get_current_user),
):

    for file in files:
        file_type = "document"
        if file.content_type.startswith("image/"):
            file_type = "image"
        elif file.content_type.startswith("video/"):
            file_type = "video"
        elif file.content_type.startswith("audio/"):
            file_type = "audio"

        cloudinary_response = upload_file(
            file.file, file_type if file_type == "image" else "auto"
        )
        file_url: str = cloudinary_response.get("secure_url", None)
        thumbnail_url = None
        if file_type == "video":
            thumbnail_url = file_url.split(".")[:-1] + ["jpg"]
            thumbnail_url = ".".join(thumbnail_url)

        # Create response object
        mime_type = cloudinary_response.get("format", "unknown")
        user_stats: UserStats | None = await UserStats.find_one(UserStats.user_id == user.id)
        tag_desc: AIResponse = tag_files({"file_url": file_url, 'mime_type': mime_type, 'file_type':file_type if file_type != 'document' else 'application'}, user_stats.tags)
        response = MediaResponse(
            user_id=user.id,
            name=tag_desc.name,
            original_filename=file.filename,
            file_type=file_type,
            file_size=file.size,
            mime_type=mime_type,
            description=tag_desc.description,
            upload_date=datetime.now(),
            tags=tag_desc.tags,
            thumbnail_url=thumbnail_url,
            width=cloudinary_response.get("width", 0),
            height=cloudinary_response.get("height", 0),
            duration=cloudinary_response.get("duration", 0),
            file_url=file_url)
        
        await media_service.add_media(response, user)
        responses.append(response)

    return responses


@router.get("/", response_model=list[MediaResponse])
async def get_all_media(type: str = 'all', user: User = Depends(get_current_user)):
    return await media_service.get_media(type, user)


@router.put("/{media_id}/tags", response_model=MediaItem)
async def update_media_tags(
    media_id: str,
    tags_update: TagsUpdate,
    user: User = Depends(get_current_user),
):
    """Update tags for a media item"""
    updated_media = await media_service.update_media_tags(media_id, tags_update.tags, user.id)
    if not updated_media:
        raise HTTPException(status_code=404, detail="Media item not found")
    return updated_media


@router.delete("/{media_id}", status_code=200)
async def delete_media_item(
    media_id: str,
    user: User = Depends(get_current_user),
):
    """Delete a media item"""
    result = await media_service.delete_media(media_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Media item not found or not accessible")
    return result


@router.post("/admin/update-all-users-tags", response_model=dict)
async def update_all_users_tags(user: User = Depends(get_current_user)):
    """Admin route to update all users' stats with tags from all their media items"""
    # Check if user is admin (you might want to add proper admin check)
    if user.id != "admin_user_id":  # Replace with actual admin check
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await media_service.update_all_users_tags()
    return {"message": "All users' tags updated successfully", "results": result}

