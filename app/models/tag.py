# app/models/tag.py
import uuid
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class InfluencerTag(SQLModel, table=True):
    __tablename__: str = "influencer_tag"

    influencer_id: uuid.UUID = Field(foreign_key="influencer.id", primary_key=True, ondelete="CASCADE")
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True, ondelete="CASCADE")


class Tag(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)


class TagCreate(BaseModel):
    name: str
