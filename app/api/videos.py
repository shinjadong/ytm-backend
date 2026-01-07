from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.youtube_service import youtube_service

router = APIRouter()

# Schemas
class VideoInfo(BaseModel):
    id: str
    title: str
    artist: str
    thumbnail: Optional[str]
    duration: int
    view_count: Optional[int] = None

class SearchResult(BaseModel):
    videos: List[VideoInfo]
    query: str
    count: int

# Routes
@router.get("/info", response_model=VideoInfo)
async def get_video_info(url: str = Query(..., description="YouTube video URL")):
    """Get video metadata"""
    try:
        info = await youtube_service.get_video_info(url)
        return VideoInfo(**info)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get video info: {str(e)}",
        )

@router.get("/search", response_model=SearchResult)
async def search_videos(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50),
):
    """Search YouTube videos"""
    try:
        videos = await youtube_service.search(q, limit)
        return SearchResult(
            videos=[VideoInfo(**v) for v in videos],
            query=q,
            count=len(videos),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Search failed: {str(e)}",
        )

@router.get("/playlist")
async def get_playlist(url: str = Query(..., description="YouTube playlist URL")):
    """Get all videos from a playlist"""
    try:
        videos = await youtube_service.get_playlist(url)
        return {
            "videos": videos,
            "count": len(videos),
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get playlist: {str(e)}",
        )
