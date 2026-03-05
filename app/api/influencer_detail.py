# app/api/influencer_detail.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
import uuid

from app.db.session import get_db
from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign
from app.models.influencer_note import InfluencerNote, NoteCreate
from app.models.tag import Tag, InfluencerTag, TagCreate
from app.core.auth import get_current_user_id
from app.services.discovery import TikTokDiscovery

router = APIRouter(dependencies=[Depends(get_current_user_id)])

def get_scraper() -> TikTokDiscovery:
    return TikTokDiscovery()


# --- Influencer Detail ---

@router.get("/influencers/{influencer_id}")
def get_influencer_detail(
    influencer_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    campaigns = db.exec(
        select(OutreachCampaign)
        .where(OutreachCampaign.influencer_id == influencer_id)
        .order_by(desc(OutreachCampaign.last_updated))
    ).all()

    notes = db.exec(
        select(InfluencerNote)
        .where(InfluencerNote.influencer_id == influencer_id)
        .order_by(desc(InfluencerNote.created_at))
    ).all()

    # Get tags via join table
    tag_rows = db.exec(
        select(Tag)
        .join(InfluencerTag, InfluencerTag.tag_id == Tag.id)
        .where(InfluencerTag.influencer_id == influencer_id)
    ).all()

    return {
        "influencer": influencer.model_dump(exclude={"campaigns"}),
        "campaigns": campaigns,
        "notes": notes,
        "tags": tag_rows,
    }


# --- Refresh Profile ---

@router.post("/influencers/{influencer_id}/refresh")
async def refresh_profile(
    influencer_id: uuid.UUID,
    db: Session = Depends(get_db),
    scraper: TikTokDiscovery = Depends(get_scraper),
):
    influencer = db.get(Influencer, influencer_id)
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
    return influencer.model_dump(exclude={"campaigns"})


# --- Notes ---

@router.post("/influencers/{influencer_id}/notes")
def add_note(
    influencer_id: uuid.UUID,
    body: NoteCreate,
    db: Session = Depends(get_db),
):
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    note = InfluencerNote(influencer_id=influencer_id, body=body.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/influencers/{influencer_id}/notes/{note_id}")
def delete_note(
    influencer_id: uuid.UUID,
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    note = db.get(InfluencerNote, note_id)
    if not note or note.influencer_id != influencer_id:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}


# --- Tags ---

@router.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    return db.exec(select(Tag).order_by(Tag.name)).all()


@router.post("/influencers/{influencer_id}/tags")
def add_tag(
    influencer_id: uuid.UUID,
    body: TagCreate,
    db: Session = Depends(get_db),
):
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    # Get or create tag
    tag = db.exec(select(Tag).where(Tag.name == body.name)).first()
    if not tag:
        tag = Tag(name=body.name)
        db.add(tag)
        db.commit()
        db.refresh(tag)

    # Check if already assigned
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
    db: Session = Depends(get_db),
):
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
    return {"ok": True}
