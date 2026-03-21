from typing import List, Optional
import json
import logging
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select, desc, col

from app.db.session import get_db
from app.services.discovery import TikTokDiscovery
from app.models.influencer import Influencer
from app.models.tag import Tag, InfluencerTag
from app.core.auth import get_current_user_id
from app.core.cache import get_redis, invalidate_cache, _CacheEncoder

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user_id)])

def get_scraper() -> TikTokDiscovery:
    return TikTokDiscovery()


@router.get("/influencers")
async def get_all_influencers(
    platform: Optional[str] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    tag: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    has_filters = any([platform, min_followers is not None, max_followers is not None, tag])
    r = get_redis()
    cache_key = f"cache:{user_id}:influencers"

    if not has_filters and r is not None:
        try:
            hit = r.get(cache_key)
            if hit is not None:
                logger.info("CACHE HIT [influencers]: serving from Redis")
                return json.loads(hit)
            logger.info("CACHE MISS [influencers]: fetching from DB")
        except Exception:
            logger.warning("Redis GET failed for influencers, falling through to DB")

    statement = select(Influencer).where(Influencer.user_id == user_id)

    if platform:
        statement = statement.where(Influencer.platform == platform)
    if min_followers is not None:
        statement = statement.where(col(Influencer.follower_count) >= min_followers)
    if max_followers is not None:
        statement = statement.where(col(Influencer.follower_count) <= max_followers)
    if tag:
        statement = (
            statement
            .join(InfluencerTag, col(InfluencerTag.influencer_id) == col(Influencer.id))
            .join(Tag, col(Tag.id) == col(InfluencerTag.tag_id))
            .where(Tag.name == tag)
        )

    statement = statement.order_by(desc(Influencer.created_at))
    results = db.exec(statement).all()
    result = [row.model_dump(exclude={"campaigns"}) for row in results]

    if not has_filters and r is not None:
        try:
            r.setex(cache_key, 30, json.dumps(result, cls=_CacheEncoder))
            logger.info("CACHE SET [influencers]: stored with TTL=30s")
        except Exception:
            logger.warning("Redis SET failed for influencers, response served uncached")

    return result


@router.post("/discover")
async def discover_influencers(
    niche: str,
    platform: str = "tiktok",
    search_type: str = "user",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    scraper: TikTokDiscovery = Depends(get_scraper)
):
    if search_type == "video":
        raw_profiles = await scraper.search_by_videos(query=niche)
    elif search_type == "hashtag":
        raw_profiles = await scraper.search_by_hashtag(hashtag=niche)
    else:
        raw_profiles = await scraper.search_profiles(query=niche)

    saved_influencers = []
    new_influencers = []

    for profile_data in raw_profiles:
        existing_influencer = db.exec(
            select(Influencer).where(
                Influencer.handle == profile_data.handle,
                Influencer.user_id == user_id,
            )
        ).first()

        if existing_influencer:
            saved_influencers.append(existing_influencer)
        else:
            new_influencer = Influencer(**profile_data.model_dump(), user_id=user_id)
            db.add(new_influencer)
            new_influencers.append(new_influencer)
            saved_influencers.append(new_influencer)

    if new_influencers:
        db.commit()
        for influencer in new_influencers:
            db.refresh(influencer)
        invalidate_cache(f"{user_id}:dashboard", f"{user_id}:influencers")

    return [i.model_dump(exclude={"campaigns"}) for i in saved_influencers]


class BulkDeleteRequest(BaseModel):
    influencer_ids: List[str]


@router.post("/influencers/bulk-delete")
def bulk_delete(
    body: BulkDeleteRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = 0
    for inf_id in body.influencer_ids:
        influencer = db.exec(
            select(Influencer).where(
                Influencer.id == uuid.UUID(inf_id),
                Influencer.user_id == user_id,
            )
        ).first()
        if influencer:
            db.delete(influencer)
            deleted += 1
    db.commit()
    invalidate_cache(f"{user_id}:dashboard", f"{user_id}:influencers")
    return {"deleted": deleted}


class BulkTagRequest(BaseModel):
    influencer_ids: List[str]
    tag_name: str


@router.post("/influencers/bulk-tag")
def bulk_tag(
    body: BulkTagRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    tag = db.exec(
        select(Tag).where(Tag.name == body.tag_name, Tag.user_id == user_id)
    ).first()
    if not tag:
        tag = Tag(name=body.tag_name, user_id=user_id)
        db.add(tag)
        db.commit()
        db.refresh(tag)

    tagged = 0
    for inf_id in body.influencer_ids:
        uid = uuid.UUID(inf_id)
        influencer = db.exec(
            select(Influencer).where(Influencer.id == uid, Influencer.user_id == user_id)
        ).first()
        if not influencer:
            continue
        existing = db.exec(
            select(InfluencerTag).where(
                InfluencerTag.influencer_id == uid,
                InfluencerTag.tag_id == tag.id,
            )
        ).first()
        if not existing:
            db.add(InfluencerTag(influencer_id=uid, tag_id=tag.id))
            tagged += 1

    db.commit()
    invalidate_cache(f"{user_id}:tags", f"{user_id}:influencers")
    return {"tagged": tagged}
