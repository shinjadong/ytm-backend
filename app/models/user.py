from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum

from app.core.database import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ULTRA = "ultra"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    username = Column(String(100), unique=True, index=True)

    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)

    # Usage tracking
    daily_downloads = Column(Integer, default=0)
    last_download_date = Column(DateTime, nullable=True)
    total_downloads = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def is_pro(self) -> bool:
        from datetime import datetime
        if self.subscription_tier == SubscriptionTier.FREE:
            return False
        if self.subscription_expires_at and self.subscription_expires_at < datetime.utcnow():
            return False
        return True

    @property
    def daily_limit(self) -> int:
        if self.is_pro:
            return 999999  # Unlimited
        return 3

    @property
    def audio_quality(self) -> str:
        if self.is_pro:
            return "320"
        return "128"
