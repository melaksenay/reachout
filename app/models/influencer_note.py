# app/models/influencer_note.py
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class InfluencerNote(SQLModel, table=True):
    __tablename__: str = "influencer_note"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    influencer_id: uuid.UUID = Field(foreign_key="influencer.id", ondelete="CASCADE")
    body: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NoteCreate(BaseModel):
    body: str
