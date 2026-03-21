# app/api/settings.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
import json
import logging

from app.db.session import get_db
from app.models.user_settings import UserSettings, UserSettingsUpdate
from app.core.auth import get_current_user_id
from app.core.cache import get_redis, invalidate_cache, _CacheEncoder

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user_id)])


@router.get("/settings")
def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    r = get_redis()
    cache_key = f"cache:{user_id}:settings"
    if r is not None:
        try:
            hit = r.get(cache_key)
            if hit is not None:
                logger.info("CACHE HIT [settings]")
                return json.loads(hit)
        except Exception:
            logger.warning("Redis GET failed for settings, falling through to DB")

    settings = db.exec(
        select(UserSettings).where(UserSettings.user_id == user_id)
    ).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    if r is not None:
        try:
            r.setex(cache_key, 600, json.dumps(settings, cls=_CacheEncoder))
        except Exception:
            logger.warning("Redis SET failed for settings")

    return settings


@router.patch("/settings")
def update_settings(
    body: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    settings = db.exec(
        select(UserSettings).where(UserSettings.user_id == user_id)
    ).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    settings.brand_description = body.brand_description
    settings.updated_at = datetime.now(timezone.utc)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    invalidate_cache(f"{user_id}:settings")
    return settings
