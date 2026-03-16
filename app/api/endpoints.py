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
    db: Session = Depends(get_db),
):
    # Only cache the unfiltered base list
    has_filters = any([platform, min_followers is not None, max_followers is not None, tag])
    r = get_redis()

    if not has_filters and r is not None:
        try:
            hit = r.get("cache:influencers")  # type: ignore[arg-type]
            if hit is not None:
                logger.info("CACHE HIT [influencers]: serving from Redis")
                return json.loads(hit)
            logger.info("CACHE MISS [influencers]: fetching from DB")
        except Exception:
            logger.warning("Redis GET failed for influencers, falling through to DB")

    statement = select(Influencer)

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
            r.setex("cache:influencers", 30, json.dumps(result, cls=_CacheEncoder))
            logger.info("CACHE SET [influencers]: stored with TTL=30s")
        except Exception:
            logger.warning("Redis SET failed for influencers, response served uncached")

    return result

# Setting response_model automatically serializes the output and filters internal fields
@router.post("/discover")
async def discover_influencers(
    niche: str,
    platform: str = "tiktok",
    search_type: str = "user",
    db: Session = Depends(get_db),
    scraper: TikTokDiscovery = Depends(get_scraper)
):

    # 1. Fetch raw profiles using the selected search method
    if search_type == "video":
        raw_profiles = await scraper.search_by_videos(query=niche)
    elif search_type == "hashtag":
        raw_profiles = await scraper.search_by_hashtag(hashtag=niche)
    else:
        raw_profiles = await scraper.search_profiles(query=niche)
    
    saved_influencers = []
    new_influencers = []
    
    for profile_data in raw_profiles:
        # 2. Execute a SQL SELECT statement to check for existing handles
        statement = select(Influencer).where(Influencer.handle == profile_data.handle)
        existing_influencer = db.exec(statement).first()

        if existing_influencer:
            saved_influencers.append(existing_influencer)
        else:
            # 3. Instantiate the SQLModel class from the validated DiscoveredProfile
            new_influencer = Influencer(**profile_data.model_dump())
            db.add(new_influencer)
            new_influencers.append(new_influencer)
            saved_influencers.append(new_influencer)
            
    # 4. Commit only if new records were added to the session
    if new_influencers:
        db.commit()
        # 5. Refresh loads the database-generated UUIDs and default values back into the Python objects
        for influencer in new_influencers:
            db.refresh(influencer)
        invalidate_cache("dashboard", "influencers")

    return [i.model_dump(exclude={"campaigns"}) for i in saved_influencers]


class BulkDeleteRequest(BaseModel):
    influencer_ids: List[str]


@router.post("/influencers/bulk-delete")
def bulk_delete(
    body: BulkDeleteRequest,
    db: Session = Depends(get_db),
):
    deleted = 0
    for inf_id in body.influencer_ids:
        influencer = db.get(Influencer, uuid.UUID(inf_id))
        if influencer:
            db.delete(influencer)
            deleted += 1
    db.commit()
    invalidate_cache("dashboard", "influencers")
    return {"deleted": deleted}


class BulkTagRequest(BaseModel):
    influencer_ids: List[str]
    tag_name: str


@router.post("/influencers/bulk-tag")
def bulk_tag(
    body: BulkTagRequest,
    db: Session = Depends(get_db),
):
    # Get or create tag
    tag = db.exec(select(Tag).where(Tag.name == body.tag_name)).first()
    if not tag:
        tag = Tag(name=body.tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)

    tagged = 0
    for inf_id in body.influencer_ids:
        uid = uuid.UUID(inf_id)
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
    invalidate_cache("tags", "influencers")
    return {"tagged": tagged}