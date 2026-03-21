# app/models/campaign.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel, Relationship

# This prevents circular imports during runtime but allows type checking
if TYPE_CHECKING:
    from app.models.influencer import Influencer

VALID_STATUSES = [
    "drafted", "sent", "replied",
    "negotiating", "closed", "rejected"
]

class OutreachCampaign(SQLModel, table=True):
    __tablename__: str = "outreach_campaign"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    influencer_id: uuid.UUID = Field(foreign_key="influencer.id", ondelete="CASCADE")
    status: str = Field(default="drafted")
    generated_message: Optional[str] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

    # This allows you to do: my_campaign.influencer.handle
    influencer: "Influencer" = Relationship(back_populates="campaigns")


class CampaignStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v


class CampaignNotesUpdate(BaseModel):
    notes: Optional[str] = None


class CampaignMessageUpdate(BaseModel):
    generated_message: str


class CampaignWithInfluencer(BaseModel):
    """Flattened response for the Kanban board — avoids N+1 by joining at query time."""
    id: uuid.UUID
    influencer_id: uuid.UUID
    influencer_handle: str
    influencer_platform: str
    influencer_url: str
    influencer_follower_count: Optional[int] = None
    status: str
    status_updated_at: datetime
    generated_message: Optional[str] = None
    notes: Optional[str] = None
    last_updated: datetime
