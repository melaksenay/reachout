# app/api/influencer_detail.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc, col
import uuid
import json
import logging

from app.db.session import get_db
from app.models.influencer import Influencer, InfluencerRead
from app.models.campaign import OutreachCampaign, CampaignRead
from app.models.influencer_note import InfluencerNote, NoteCreate
from app.models.tag import Tag, InfluencerTag, TagCreate
from app.core.auth import get_current_user_id
from app.core.cache import get_redis, invalidate_cache, _CacheEncoder
from app.services.discovery import TikTokDiscovery

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user_id)])

def get_scraper() -> TikTokDiscovery:
    return TikTokDiscovery()


# --- Influencer Detail ---

@router.get("/influencers/{influencer_id}")
def get_influencer_detail(
    influencer_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    influencer = db.exec(
        select(Influencer).where(Influencer.id == influencer_id, Influencer.user_id == user_id)
    ).first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    campaigns = db.exec(
        select(OutreachCampaign)
        .where(
            OutreachCampaign.influencer_id == influencer_id,
            OutreachCampaign.user_id == user_id,
        )
        .order_by(desc(OutreachCampaign.last_updated))
    ).all()

    notes = db.exec(
        select(InfluencerNote)
        .where(
            InfluencerNote.influencer_id == influencer_id,
            InfluencerNote.user_id == user_id,
        )
        .order_by(desc(InfluencerNote.created_at))
    ).all()

    tag_rows = db.exec(
        select(Tag)
        .join(InfluencerTag, col(InfluencerTag.tag_id) == col(Tag.id))
        .where(InfluencerTag.influencer_id == influencer_id, Tag.user_id == user_id)
    ).all()

    return {
        "influencer": InfluencerRead.model_validate(influencer),
        "campaigns": [CampaignRead.model_validate(c) for c in campaigns],
        "notes": notes,
        "tags": tag_rows,
    }


# --- Refresh Profile ---

@router.post("/influencers/{influencer_id}/refresh")
async def refresh_profile(
    influencer_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    scraper: TikTokDiscovery = Depends(get_scraper),
):
    influencer = db.exec(
        select(Influencer).where(Influencer.id == influencer_id, Influencer.user_id == user_id)
    ).first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    data = await scraper.scrape_profile(influencer.handle)

    if data.get("bio"):
        influencer.bio_text = data["bio"]
    if data.get("follower_count"):
        influencer.follower_count = data["follower_count"]

    db.add(influencer)
    db.commit()
    db.refresh(influencer)
    invalidate_cache(f"{user_id}:influencers")
    return InfluencerRead.model_validate(influencer)


# --- Notes ---

@router.post("/influencers/{influencer_id}/notes")
def add_note(
    influencer_id: uuid.UUID,
    body: NoteCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    influencer = db.exec(
        select(Influencer).where(Influencer.id == influencer_id, Influencer.user_id == user_id)
    ).first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    note = InfluencerNote(influencer_id=influencer_id, user_id=user_id, body=body.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/influencers/{influencer_id}/notes/{note_id}")
def delete_note(
    influencer_id: uuid.UUID,
    note_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    note = db.exec(
        select(InfluencerNote).where(
            InfluencerNote.id == note_id,
            InfluencerNote.influencer_id == influencer_id,
            InfluencerNote.user_id == user_id,
        )
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}


# --- Tags ---

@router.get("/tags")
def list_tags(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    r = get_redis()
    cache_key = f"cache:{user_id}:tags"
    if r is not None:
        try:
            hit = r.get(cache_key)
            if hit is not None:
                logger.info("CACHE HIT [tags]")
                return json.loads(hit)
        except Exception:
            logger.warning("Redis GET failed for tags, falling through to DB")

    tags = db.exec(select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)).all()

    if r is not None:
        try:
            r.setex(cache_key, 300, json.dumps(tags, cls=_CacheEncoder))
        except Exception:
            logger.warning("Redis SET failed for tags")

    return tags


@router.post("/influencers/{influencer_id}/tags")
def add_tag(
    influencer_id: uuid.UUID,
    body: TagCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    influencer = db.exec(
        select(Influencer).where(Influencer.id == influencer_id, Influencer.user_id == user_id)
    ).first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    tag = db.exec(
        select(Tag).where(Tag.name == body.name, Tag.user_id == user_id)
    ).first()
    if not tag:
        tag = Tag(name=body.name, user_id=user_id)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        invalidate_cache(f"{user_id}:tags")

    existing = db.exec(
        select(InfluencerTag).where(
            InfluencerTag.influencer_id == influencer_id,
            InfluencerTag.tag_id == tag.id,
        )
    ).first()
    if not existing:
        link = InfluencerTag(influencer_id=influencer_id, tag_id=tag.id)
        db.add(link)
        db.commit()
        db.refresh(tag)

    return tag


@router.delete("/influencers/{influencer_id}/tags/{tag_id}")
def remove_tag(
    influencer_id: uuid.UUID,
    tag_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    tag = db.exec(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    link = db.exec(
        select(InfluencerTag).where(
            InfluencerTag.influencer_id == influencer_id,
            InfluencerTag.tag_id == tag_id,
        )
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Tag not assigned")
    db.delete(link)
    db.commit()
    invalidate_cache(f"{user_id}:tags")
    return {"ok": True}
