from fastapi import APIRouter, HTTPException, status, Depends
from src.models.user import User
from src.utils.auth import get_current_user
from src.schemas.ai import (
    AIProcessRequest,
    AIProcessResponse,
    AIStatusResponse,
    AITagsResponse,
    AIOCRResponse,
    AITranscriptionResponse,
    AIDescriptionResponse,
    AICustomPromptRequest,
    AICustomPromptResponse,
)
from src.ai.pyd_ai import (
    tag_files,
    ocr_text_extraction,
    object_scene_recognition,
    file_summarization,
    audio_transcription,
    emotion_analysis,
    speaker_identification,
    object_face_recognition,
)
from src.models.media_item import MediaItem
from uuid import uuid4
from typing import Dict, Any
import asyncio

# In-memory storage for AI jobs (in a real app, this would be in a database)
ai_jobs: Dict[str, Dict[str, Any]] = {}

router = APIRouter(
    prefix="/ai",
    tags=["AI Processing"],
    responses={404: {"description": "Not found"}},
)


@router.post("/process", response_model=AIProcessResponse)
async def process_media(
    request: AIProcessRequest, current_user: User = Depends(get_current_user)
):
    """Process media with AI"""
    # Create a new job ID
    job_id = str(uuid4())

    # Store job in memory (in a real app, this would be in a database)
    ai_jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "mediaIds": request.mediaIds,
        "options": request.options,
        "user_id": current_user.id,
        "results": {},
    }

    # Start background processing
    asyncio.create_task(process_media_items(job_id))

    return AIProcessResponse(jobId=job_id, status="queued", mediaIds=request.mediaIds)


@router.get("/status/{job_id}", response_model=AIStatusResponse)
async def get_processing_status(
    job_id: str, current_user: User = Depends(get_current_user)
):
    """Get AI processing status"""
    # Check if job exists
    if job_id not in ai_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Check if job belongs to user
    job = ai_jobs[job_id]
    if job["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job",
        )

    return AIStatusResponse(
        jobId=job_id,
        status=job["status"],
        progress=job["progress"],
        results=job.get("results"),
    )


@router.post("/tags/{media_id}", response_model=AITagsResponse)
async def generate_tags(media_id: str, current_user: User = Depends(get_current_user)):
    """Generate AI tags for media"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = tag_files(file_info, media.tags if hasattr(media, "tags") else [])

    # Update media tags in database
    media.tags = ai_response.tags
    await media.save()

    return AITagsResponse(mediaId=media_id, tags=ai_response.tags)


@router.post("/ocr/{media_id}", response_model=AIOCRResponse)
async def perform_ocr(media_id: str, current_user: User = Depends(get_current_user)):
    """Perform OCR on document or image"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    if media.file_type not in ["image", "document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OCR can only be performed on images or documents",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = ocr_text_extraction(file_info)

    return AIOCRResponse(
        mediaId=media_id, text=ai_response.text, confidence=ai_response.confidence
    )


@router.post("/transcribe/{media_id}", response_model=AITranscriptionResponse)
async def transcribe_media(
    media_id: str, current_user: User = Depends(get_current_user)
):
    """Transcribe audio or video"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    if media.file_type not in ["video", "audio"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription can only be performed on audio or video files",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = audio_transcription(file_info)

    # Create segments from the text
    segments = [
        {"start": 0, "end": 5, "text": ai_response.text[:100]},
        {
            "start": 5,
            "end": 10,
            "text": ai_response.text[100:200] if len(ai_response.text) > 100 else "",
        },
        {
            "start": 10,
            "end": 15,
            "text": ai_response.text[200:300] if len(ai_response.text) > 200 else "",
        },
    ]

    return AITranscriptionResponse(
        mediaId=media_id, transcript=ai_response.text, segments=segments
    )


@router.post("/describe/{media_id}", response_model=AIDescriptionResponse)
async def generate_description(
    media_id: str, current_user: User = Depends(get_current_user)
):
    """Generate AI description for media"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = tag_files(file_info, media.tags if hasattr(media, "tags") else [])

    # Update media description in database
    media.description = ai_response.description
    await media.save()

    return AIDescriptionResponse(mediaId=media_id, description=ai_response.description)


@router.post("/custom", response_model=AICustomPromptResponse)
async def process_with_prompt(
    request: AICustomPromptRequest, current_user: User = Depends(get_current_user)
):
    """Process media with custom AI prompt"""
    # Create a new job ID
    job_id = str(uuid4())

    # Store job in memory
    ai_jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "mediaIds": request.mediaIds,
        "prompt": request.prompt,
        "user_id": current_user.id,
        "results": {},
    }

    # Start background processing
    asyncio.create_task(process_custom_prompt(job_id, request.prompt))

    return AICustomPromptResponse(jobId=job_id, status="queued")


@router.post("/object-recognition/{media_id}", response_model=AIOCRResponse)
async def process_object_recognition(
    media_id: str, current_user: User = Depends(get_current_user)
):
    """Perform object/face recognition on media"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    if media.file_type not in ["image", "video"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Object recognition can only be performed on images or videos",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    if media.file_type == "image":
        ai_response = object_face_recognition(file_info)
    else:
        ai_response = object_scene_recognition(file_info)

    return AIOCRResponse(
        mediaId=media_id, text=ai_response.text, confidence=ai_response.confidence
    )


@router.post("/summarize/{media_id}", response_model=AIOCRResponse)
async def summarize_media(
    media_id: str, current_user: User = Depends(get_current_user)
):
    """Summarize video or document"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    if media.file_type not in ["video", "document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summarization can only be performed on videos or documents",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = file_summarization(file_info)

    return AIOCRResponse(
        mediaId=media_id, text=ai_response.text, confidence=ai_response.confidence
    )


@router.post("/emotion-analysis/{media_id}", response_model=AIOCRResponse)
async def analyze_emotion(
    media_id: str, current_user: User = Depends(get_current_user)
):
    """Analyze emotions in audio"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    if media.file_type != "audio":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emotion analysis can only be performed on audio files",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = emotion_analysis(file_info)

    return AIOCRResponse(
        mediaId=media_id, text=ai_response.text, confidence=ai_response.confidence
    )


@router.post("/speaker-identification/{media_id}", response_model=AIOCRResponse)
async def identify_speakers(
    media_id: str, current_user: User = Depends(get_current_user)
):
    """Identify speakers in audio"""
    # Check if media exists and belongs to user
    media = await MediaItem.find_one(MediaItem.id == media_id)
    if not media or media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found or not accessible",
        )

    if media.file_type != "audio":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Speaker identification can only be performed on audio files",
        )

    # Process with AI
    file_info = {
        "file_url": media.file_url,
        "file_type": media.file_type
        if media.file_type != "document"
        else "application",
        "mime_type": media.mime_type,
    }

    ai_response = speaker_identification(file_info)

    return AIOCRResponse(
        mediaId=media_id, text=ai_response.text, confidence=ai_response.confidence
    )


# Helper function to process media items
async def process_media_items(job_id: str):
    """Process media items for a job"""
    job = ai_jobs[job_id]
    job["status"] = "processing"

    media_ids = job["mediaIds"]
    options = job["options"]
    results = {}

    total_items = len(media_ids)
    processed = 0

    for media_id in media_ids:
        try:
            # Get media from database
            media = await MediaItem.find_one(MediaItem.id == media_id)
            if not media or media.user_id != job["user_id"]:
                results[media_id] = {"error": "Media not found or not accessible"}
                continue

            file_info = {
                "file_url": media.file_url,
                "file_type": media.file_type
                if media.file_type != "document"
                else "application",
                "mime_type": media.mime_type,
            }

            # Process based on options and media type
            media_results = {}

            # For images
            if media.file_type == "image":
                if options.get("recognition", False):
                    media_results["recognition"] = object_face_recognition(file_info)
                if options.get("ocr", False):
                    ocr_response = ocr_text_extraction(file_info)
                    media_results["ocr"] = {
                        "text": ocr_response.text,
                        "confidence": ocr_response.confidence,
                    }
                if options.get("tagging", False):
                    tag_response = tag_files(
                        file_info, media.tags if hasattr(media, "tags") else []
                    )
                    media_results["tagging"] = {"tags": tag_response.tags}
                    # Update media in database
                    media.tags = tag_response.tags
                    await media.save()

            # For videos
            elif media.file_type == "video":
                if options.get("recognition", False):
                    media_results["recognition"] = object_scene_recognition(file_info)
                if options.get("transcription", False):
                    trans_response = audio_transcription(file_info)
                    media_results["transcription"] = {"text": trans_response.text}
                if options.get("summarization", False):
                    media_results["summarization"] = file_summarization(file_info)

            # For audio
            elif media.file_type == "audio":
                if options.get("transcription", False):
                    trans_response = audio_transcription(file_info)
                    media_results["transcription"] = {"text": trans_response.text}
                if options.get("emotion", False):
                    media_results["emotion"] = emotion_analysis(file_info)
                if options.get("speaker", False):
                    media_results["speaker"] = speaker_identification(file_info)

            # For documents
            elif media.file_type == "document":
                if options.get("ocr", False):
                    ocr_response = ocr_text_extraction(file_info)
                    media_results["ocr"] = {
                        "text": ocr_response.text,
                        "confidence": ocr_response.confidence,
                    }
                if options.get("summarization", False):
                    media_results["summarization"] = file_summarization(file_info)

            results[media_id] = media_results

        except Exception as e:
            results[media_id] = {"error": str(e)}

        # Update progress
        processed += 1
        job["progress"] = (processed / total_items) * 100
        await asyncio.sleep(0.5)  # Small delay to prevent CPU hogging

    # Set job as completed
    job["status"] = "completed"
    job["progress"] = 100
    job["results"] = results


# Helper function to process custom prompts
async def process_custom_prompt(job_id: str, prompt: str):
    """Process media with custom prompt"""
    job = ai_jobs[job_id]
    job["status"] = "processing"

    media_ids = job["mediaIds"]
    results = {}

    total_items = len(media_ids)
    processed = 0

    for media_id in media_ids:
        try:
            # Get media from database
            media = await MediaItem.find_one(MediaItem.id == media_id)
            if not media or media.user_id != job["user_id"]:
                results[media_id] = {"error": "Media not found or not accessible"}
                continue

            # Process with custom prompt using appropriate AI function based on media type
            # In a real implementation, you would use a more generic AI function that accepts custom prompts
            # For now, we'll use the existing functions as a fallback
            file_info = {
                "file_url": media.file_url,
                "file_type": media.file_type
                if media.file_type != "document"
                else "application",
                "mime_type": media.mime_type,
            }

            if media.file_type in ["image", "document"]:
                response = tag_files(
                    file_info, media.tags if hasattr(media, "tags") else []
                )
                results[media_id] = {
                    "description": response.description,
                    "tags": response.tags,
                }
            elif media.file_type in ["video", "audio"]:
                response = audio_transcription(file_info)
                results[media_id] = {"text": response.text}

        except Exception as e:
            results[media_id] = {"error": str(e)}

        # Update progress
        processed += 1
        job["progress"] = (processed / total_items) * 100
        await asyncio.sleep(0.5)  # Small delay to prevent CPU hogging

    # Set job as completed
    job["status"] = "completed"
    job["progress"] = 100
    job["results"] = results
