# app/api/campaigns.py
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
import uuid

from app.db.session import get_db
from app.models.influencer import Influencer
from app.models.campaign import (
    OutreachCampaign,
    CampaignStatusUpdate,
    CampaignNotesUpdate,
    CampaignMessageUpdate,
    CampaignWithInfluencer,
)
from app.models.user_settings import UserSettings
from app.services.discovery import TikTokDiscovery
from app.services.ai_outreach import AIOutreachService

router = APIRouter()


@router.get("/campaigns", response_model=List[CampaignWithInfluencer])
def get_all_campaigns(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    statement = (
        select(OutreachCampaign, Influencer)
        .join(Influencer, OutreachCampaign.influencer_id == Influencer.id)
        .order_by(desc(OutreachCampaign.last_updated))
    )
    if status:
        statement = statement.where(OutreachCampaign.status == status)
    rows = db.exec(statement).all()
    return [
        CampaignWithInfluencer(
            id=campaign.id,
            influencer_id=campaign.influencer_id,
            influencer_handle=inf.handle,
            influencer_platform=inf.platform,
            influencer_url=inf.url,
            influencer_follower_count=inf.follower_count,
            status=campaign.status,
            status_updated_at=campaign.status_updated_at,
            generated_message=campaign.generated_message,
            notes=campaign.notes,
            last_updated=campaign.last_updated,
        )
        for campaign, inf in rows
    ]


@router.patch("/campaigns/{campaign_id}/status", response_model=OutreachCampaign)
def update_campaign_status(
    campaign_id: uuid.UUID,
    body: CampaignStatusUpdate,
    db: Session = Depends(get_db),
):
    campaign = db.get(OutreachCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = body.status
    campaign.status_updated_at = datetime.now(timezone.utc)
    campaign.last_updated = datetime.now(timezone.utc)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.patch("/campaigns/{campaign_id}/notes", response_model=OutreachCampaign)
def update_campaign_notes(
    campaign_id: uuid.UUID,
    body: CampaignNotesUpdate,
    db: Session = Depends(get_db),
):
    campaign = db.get(OutreachCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.notes = body.notes
    campaign.last_updated = datetime.now(timezone.utc)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.patch("/campaigns/{campaign_id}/message", response_model=OutreachCampaign)
def update_campaign_message(
    campaign_id: uuid.UUID,
    body: CampaignMessageUpdate,
    db: Session = Depends(get_db),
):
    campaign = db.get(OutreachCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.generated_message = body.generated_message
    campaign.last_updated = datetime.now(timezone.utc)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/campaigns/{influencer_id}/draft")
async def draft_campaign(
    influencer_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    # 1. Fetch the influencer
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    # 2. Check if a campaign already exists to avoid duplicates
    existing = db.exec(
        select(OutreachCampaign).where(OutreachCampaign.influencer_id == influencer_id)
    ).first()
    if existing:
        return existing

    # 3. Fetch brand description from settings
    settings = db.exec(
        select(UserSettings).where(UserSettings.key == "default")
    ).first()
    brand_description = settings.brand_description if settings else None

    if not brand_description:
        raise HTTPException(
            status_code=400,
            detail="Brand description not set. Go to Settings first."
        )

    # 4. Scrape the influencer's TikTok profile for context
    discovery = TikTokDiscovery()
    profile_context = await discovery.scrape_profile(influencer.handle)

    # 5. Generate personalized message via Claude
    ai_service = AIOutreachService()
    draft_text = ai_service.generate_message(influencer, brand_description, profile_context)

    new_campaign = OutreachCampaign(
        influencer_id=influencer.id,
        generated_message=draft_text,
        status="drafted",
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    return new_campaign
