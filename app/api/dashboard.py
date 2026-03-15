# app/api/dashboard.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select, desc, func

from app.db.session import get_db
from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign, CampaignWithInfluencer, VALID_STATUSES
from app.core.auth import get_current_user_id

router = APIRouter(dependencies=[Depends(get_current_user_id)])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    # Total influencers
    total_influencers = db.exec(
        select(func.count()).select_from(Influencer)
    ).one()

    # Campaigns grouped by status
    status_rows = db.exec(
        select(OutreachCampaign.status, func.count())
        .group_by(OutreachCampaign.status)
    ).all()
    campaigns_by_status = {s: 0 for s in VALID_STATUSES}
    for status, count in status_rows:
        campaigns_by_status[status] = count
    total_campaigns = sum(campaigns_by_status.values())

    # Response rate: replied + negotiating + closed / total
    engaged = (
        campaigns_by_status.get("replied", 0)
        + campaigns_by_status.get("negotiating", 0)
        + campaigns_by_status.get("closed", 0)
    )
    response_rate = round(engaged / total_campaigns, 2) if total_campaigns > 0 else 0

    # Recent 5 campaigns with influencer info
    recent_rows = db.exec(
        select(OutreachCampaign, Influencer)
        .join(Influencer, col(OutreachCampaign.influencer_id) == col(Influencer.id))
        .order_by(desc(OutreachCampaign.last_updated))
        .limit(5)
    ).all()
    recent_campaigns = [
        CampaignWithInfluencer(
            id=c.id,
            influencer_id=c.influencer_id,
            influencer_handle=inf.handle,
            influencer_platform=inf.platform,
            influencer_url=inf.url,
            influencer_follower_count=inf.follower_count,
            status=c.status,
            status_updated_at=c.status_updated_at,
            generated_message=c.generated_message,
            notes=c.notes,
            last_updated=c.last_updated,
        )
        for c, inf in recent_rows
    ]

    return {
        "total_influencers": total_influencers,
        "total_campaigns": total_campaigns,
        "campaigns_by_status": campaigns_by_status,
        "response_rate": response_rate,
        "recent_campaigns": recent_campaigns,
    }
