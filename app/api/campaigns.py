# app/api/campaigns.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import uuid

from app.db.session import get_db
from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign
from app.services.outreach import OutreachService

router = APIRouter()

@router.post("/campaigns/{influencer_id}/draft")
def draft_campaign(
    influencer_id: uuid.UUID,
    db: Session = Depends(get_db),
    outreach_service: OutreachService = Depends() # Simple DI for the service
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

    # 3. Create the draft
    draft_text = outreach_service.create_initial_draft(influencer)
    
    new_campaign = OutreachCampaign(
        influencer_id=influencer.id,
        generated_message=draft_text,
        status="drafted"
    )
    
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    
    return new_campaign