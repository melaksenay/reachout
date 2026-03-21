# app/models/tag.py
import uuid
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class InfluencerTag(SQLModel, table=True):
    __tablename__: str = "influencer_tag"

    influencer_id: uuid.UUID = Field(foreign_key="influencer.id", primary_key=True, ondelete="CASCADE")
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True, ondelete="CASCADE")


class Tag(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tag_user_name"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    name: str = Field(index=True)


class TagCreate(BaseModel):
    name: str
