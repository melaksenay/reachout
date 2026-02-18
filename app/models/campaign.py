# app/models/campaign.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid
from sqlmodel import Field, SQLModel, Relationship

# This prevents circular imports during runtime but allows type checking
if TYPE_CHECKING:
    from app.models.influencer import Influencer

class OutreachCampaign(SQLModel, table=True):
    __tablename__: str = "outreach_campaign"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    influencer_id: uuid.UUID = Field(foreign_key="influencer.id", ondelete="CASCADE")
    status: str = Field(default="discovered")
    generated_message: Optional[str] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # This allows you to do: my_campaign.influencer.handle
    influencer: "Influencer" = Relationship(back_populates="campaigns")