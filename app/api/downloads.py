from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.download import Download, DownloadStatus
from app.services.youtube_service import youtube_service

router = APIRouter()

# Schemas
class DownloadRequest(BaseModel):
    video_id: str
    url: Optional[str] = None

class DownloadResponse(BaseModel):
    id: int
    video_id: str
    title: Optional[str]
    artist: Optional[str]
    status: DownloadStatus
    quality: str
    download_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DownloadListResponse(BaseModel):
    downloads: List[DownloadResponse]
    total: int

# Background task
async def process_download(download_id: int, video_id: str, quality: str):
    """Background task to process download"""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Download).where(Download.id == download_id))
        download = result.scalar_one_or_none()

        if not download:
            return

        try:
            download.status = DownloadStatus.PROCESSING
            await db.commit()

            # Download and convert
            result = await youtube_service.download_audio(video_id, quality)

            download.status = DownloadStatus.COMPLETED
            download.file_path = result['file_path']
            download.file_size = result['file_size']
            download.title = result['title']
            download.artist = result['artist']
            download.completed_at = datetime.utcnow()
            download.expires_at = datetime.utcnow() + timedelta(hours=settings.MAX_FILE_AGE_HOURS)
            download.download_url = f"/api/downloads/{download.id}/file"

            await db.commit()

        except Exception as e:
            download.status = DownloadStatus.FAILED
            download.error_message = str(e)[:500]
            download.retry_count += 1
            await db.commit()

# Routes
@router.post("/", response_model=DownloadResponse)
async def create_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new download request"""
    user_id = int(current_user.get("sub"))

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check daily limit
    today = datetime.utcnow().date()
    if user.last_download_date and user.last_download_date.date() < today:
        user.daily_downloads = 0

    if user.daily_downloads >= user.daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily download limit ({user.daily_limit}) reached. Upgrade to Pro for unlimited downloads.",
        )

    # Get video info
    try:
        url = request.url or f"https://www.youtube.com/watch?v={request.video_id}"
        info = await youtube_service.get_video_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid video: {str(e)}")

    # Create download record
    download = Download(
        user_id=user_id,
        video_id=request.video_id,
        title=info['title'],
        artist=info['artist'],
        thumbnail_url=info['thumbnail'],
        duration_seconds=info['duration'],
        quality=user.audio_quality,
        status=DownloadStatus.PENDING,
    )
    db.add(download)

    # Update user stats
    user.daily_downloads += 1
    user.total_downloads += 1
    user.last_download_date = datetime.utcnow()

    await db.commit()
    await db.refresh(download)

    # Start background download
    background_tasks.add_task(
        process_download,
        download.id,
        request.video_id,
        user.audio_quality,
    )

    return download

@router.get("/", response_model=DownloadListResponse)
async def list_downloads(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List user's downloads"""
    user_id = int(current_user.get("sub"))

    result = await db.execute(
        select(Download)
        .where(Download.user_id == user_id)
        .order_by(Download.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    downloads = result.scalars().all()

    return DownloadListResponse(
        downloads=downloads,
        total=len(downloads),
    )

@router.get("/{download_id}", response_model=DownloadResponse)
async def get_download(
    download_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get download status"""
    user_id = int(current_user.get("sub"))

    result = await db.execute(
        select(Download).where(
            Download.id == download_id,
            Download.user_id == user_id,
        )
    )
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(status_code=404, detail="Download not found")

    return download

@router.get("/{download_id}/file")
async def download_file(
    download_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the converted file"""
    user_id = int(current_user.get("sub"))

    result = await db.execute(
        select(Download).where(
            Download.id == download_id,
            Download.user_id == user_id,
        )
    )
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(status_code=404, detail="Download not found")

    if download.status != DownloadStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Download not ready")

    if not download.file_path or not os.path.exists(download.file_path):
        raise HTTPException(status_code=404, detail="File not found or expired")

    filename = f"{download.title or 'audio'}.mp3"

    return FileResponse(
        download.file_path,
        media_type="audio/mpeg",
        filename=filename,
    )

@router.delete("/{download_id}")
async def delete_download(
    download_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a download"""
    user_id = int(current_user.get("sub"))

    result = await db.execute(
        select(Download).where(
            Download.id == download_id,
            Download.user_id == user_id,
        )
    )
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(status_code=404, detail="Download not found")

    # Delete file if exists
    if download.file_path and os.path.exists(download.file_path):
        os.remove(download.file_path)

    await db.delete(download)
    await db.commit()

    return {"message": "Download deleted"}
