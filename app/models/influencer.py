# app/models/influencer.py
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from app.models.campaign import OutreachCampaign


class DiscoveredProfile(BaseModel):
    """Validated output from TikTokDiscovery.search_profiles().
    Field names must match the Influencer table schema exactly."""
    platform: str
    handle: str
    url: str
    bio_text: Optional[str] = None
    follower_count: Optional[int] = None


class Influencer(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "handle", name="uq_influencer_user_handle"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    platform: str
    handle: str = Field(index=True)
    url: str
    bio_text: Optional[str] = None
    follower_count: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    campaigns: List["OutreachCampaign"] = Relationship(back_populates="influencer")