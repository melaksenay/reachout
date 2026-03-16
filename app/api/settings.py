# app/api/settings.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_db
from app.models.user_settings import UserSettings, UserSettingsUpdate
from app.core.auth import get_current_user_id
from app.core.cache import cached, invalidate_cache

router = APIRouter(dependencies=[Depends(get_current_user_id)])


@router.get("/settings")
@cached("settings", ttl_seconds=600)
def get_settings(db: Session = Depends(get_db)):
    settings = db.exec(
        select(UserSettings).where(UserSettings.key == "default")
    ).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.patch("/settings")
def update_settings(
    body: UserSettingsUpdate,
    db: Session = Depends(get_db),
):
    settings = db.exec(
        select(UserSettings).where(UserSettings.key == "default")
    ).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    settings.brand_description = body.brand_description
    settings.updated_at = datetime.now(timezone.utc)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    invalidate_cache("settings")
    return settings
