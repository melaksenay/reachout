# app/models/user_settings.py
from typing import Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserSettings(SQLModel, table=True):
    __tablename__: str = "user_settings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(unique=True, index=True)
    key: Optional[str] = Field(default=None)
    brand_description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSettingsUpdate(BaseModel):
    brand_description: str
