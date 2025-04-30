from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional




class AIProcessRequest(BaseModel):
    """Schema for AI processing request"""
    mediaIds: List[str] = Field(..., description="List of media IDs to process")
    options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class AIProcessResponse(BaseModel):
    """Schema for AI processing response"""
    jobId: str = Field(..., description="Processing job ID")
    status: str = Field(default="queued", description="Processing status")
    mediaIds: List[str] = Field(..., description="List of media IDs being processed")


class AIStatusResponse(BaseModel):
    """Schema for AI processing status response"""
    jobId: str = Field(..., description="Processing job ID")
    status: str = Field(..., description="Processing status")
    progress: float = Field(..., description="Processing progress (0-100)")
    results: Optional[Dict[str, Any]] = Field(None, description="Processing results")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class AITagsResponse(BaseModel):
    """Schema for AI tags response"""
    mediaId: str = Field(..., description="Media ID")
    tags: List[str] = Field(..., description="Generated tags")

class AIEmotionResponse(BaseModel):
    """Schema for AI emotion response"""
    mediaId: str = Field(..., description="Media ID")
    emotions_and_time: dict[str, str] = Field(..., description="Detected emotion and time detected")
    confidence: float = Field(..., description="Emotion confidence score")

class AIOCRResponse(BaseModel):
    """Schema for AI OCR response"""
    mediaId: str = Field(..., description="Media ID")
    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., description="OCR confidence score")


class AITranscriptionResponse(BaseModel):
    """Schema for AI transcription response"""
    mediaId: str = Field(..., description="Media ID")
    transcript: str = Field(..., description="Generated transcript")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Transcript segments with timestamps")


class AIDescriptionResponse(BaseModel):
    """Schema for AI description response"""
    mediaId: str = Field(..., description="Media ID")
    description: str = Field(..., description="Generated description")


class AICustomPromptRequest(BaseModel):
    """Schema for custom AI prompt request"""
    mediaIds: List[str] = Field(..., description="List of media IDs to process")
    prompt: str = Field(..., description="Custom AI prompt")


class AICustomPromptResponse(BaseModel):
    """Schema for custom AI prompt response"""
    jobId: str = Field(..., description="Processing job ID")
    status: str = Field(default="queued", description="Processing status")
    
class AIResponse(BaseModel):
    """Schema for AI response"""
    name: str = Field(...,  description="Suitable name of the media")
    tags: list[str] = Field(..., description="List of tags the media belongs to")
    description: str = Field(..., description="Detailed description of the media")