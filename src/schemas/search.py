from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SearchResult(BaseModel):
    """Schema for search result item"""
    id: str = Field(..., description="Item ID")
    type: str = Field(..., description="Item type (media, collection, etc.)")
    title: str = Field(..., description="Item title")
    description: Optional[str] = Field(None, description="Item description")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SearchResponse(BaseModel):
    """Schema for search response"""
    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Total number of results")
    results: List[SearchResult] = Field(..., description="Search results")


class AdvancedSearchRequest(BaseModel):
    """Schema for advanced search request"""
    query: Optional[str] = Field(None, description="Search query")
    media_types: Optional[List[str]] = Field(None, description="Media types to include")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by")
    collections: Optional[List[str]] = Field(None, description="Collections to search in")
    sort_by: Optional[str] = Field("relevance", description="Sort results by")
    sort_order: Optional[str] = Field("desc", description="Sort order")
    page: int = Field(1, description="Page number")
    page_size: int = Field(20, description="Results per page")