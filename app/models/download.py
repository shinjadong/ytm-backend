from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base

class DownloadStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Video info
    video_id = Column(String(20), nullable=False, index=True)
    title = Column(String(500))
    artist = Column(String(255))
    thumbnail_url = Column(String(500))
    duration_seconds = Column(Integer)

    # Download info
    status = Column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
    quality = Column(String(10), default="128")
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    download_url = Column(String(500), nullable=True)

    # Error tracking
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="downloads")
