from fastapi import APIRouter, HTTPException, status, Depends, Query
from src.models.user import User
from src.utils.auth import get_current_user
from src.schemas.search import SearchResponse, AdvancedSearchRequest, SearchResult
from typing import List, Optional

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=SearchResponse)
async def global_search(
    query: str = Query(..., description="Search query"),
    current_user: User = Depends(get_current_user)
):
    """Global search across all content"""
    # In a real app, we would search the database for matching content
    # Here we'll return mock results
    
    # Simulate search results
    results = [
        SearchResult(
            id="media1",
            type="media",
            title="Mountain Landscape",
            description="Beautiful mountain landscape at sunset",
            thumbnail_url="https://example.com/thumbnails/mountain.jpg",
            metadata={
                "file_type": "image/jpeg",
                "size": 1024000,
                "created_at": "2023-06-15T10:30:00Z"
            }
        ),
        SearchResult(
            id="collection1",
            type="collection",
            title="Nature Collection",
            description="Collection of nature photos",
            thumbnail_url="https://example.com/thumbnails/nature.jpg",
            metadata={
                "item_count": 15,
                "created_at": "2023-05-20T14:45:00Z"
            }
        ),
        SearchResult(
            id="media2",
            type="media",
            title="City Skyline",
            description="Urban city skyline at night",
            thumbnail_url="https://example.com/thumbnails/city.jpg",
            metadata={
                "file_type": "image/jpeg",
                "size": 2048000,
                "created_at": "2023-06-10T18:20:00Z"
            }
        )
    ]
    
    return SearchResponse(
        query=query,
        total_results=len(results),
        results=results
    )


@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(
    search_params: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Advanced search with filters"""
    # In a real app, we would apply all the filters to the database query
    # Here we'll return mock results
    
    # Simulate search results
    results = [
        SearchResult(
            id="media1",
            type="media",
            title="Mountain Landscape",
            description="Beautiful mountain landscape at sunset",
            thumbnail_url="https://example.com/thumbnails/mountain.jpg",
            metadata={
                "file_type": "image/jpeg",
                "size": 1024000,
                "created_at": "2023-06-15T10:30:00Z",
                "tags": ["nature", "mountain", "sunset"]
            }
        ),
        SearchResult(
            id="media3",
            type="media",
            title="Forest Path",
            description="Serene path through a dense forest",
            thumbnail_url="https://example.com/thumbnails/forest.jpg",
            metadata={
                "file_type": "image/jpeg",
                "size": 1536000,
                "created_at": "2023-06-05T09:15:00Z",
                "tags": ["nature", "forest", "path"]
            }
        )
    ]
    
    # Apply pagination (simulated)
    start_idx = (search_params.page - 1) * search_params.page_size
    end_idx = start_idx + search_params.page_size
    paginated_results = results[start_idx:end_idx]
    
    return SearchResponse(
        query=search_params.query or "",
        total_results=len(results),
        results=paginated_results
    )