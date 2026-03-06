"""Tests for app/api/campaigns.py routes."""
import pytest
from httpx import AsyncClient
from sqlmodel import Session

from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign


@pytest.fixture()
def sample_campaign(db: Session, sample_influencer: Influencer) -> OutreachCampaign:
    """Insert and return a sample campaign."""
    campaign = OutreachCampaign(
        influencer_id=sample_influencer.id,
        status="drafted",
        generated_message="Hey! Let's collab.",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@pytest.mark.asyncio
async def test_get_campaigns_empty(client: AsyncClient):
    resp = await client.get("/api/v1/campaigns")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_update_campaign_status(client: AsyncClient, sample_campaign):
    cid = str(sample_campaign.id)
    resp = await client.patch(
        f"/api/v1/campaigns/{cid}/status",
        json={"status": "sent"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_update_campaign_invalid_status(client: AsyncClient, sample_campaign):
    cid = str(sample_campaign.id)
    resp = await client.patch(
        f"/api/v1/campaigns/{cid}/status",
        json={"status": "invalid"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_campaign_notes(client: AsyncClient, sample_campaign):
    cid = str(sample_campaign.id)
    resp = await client.patch(
        f"/api/v1/campaigns/{cid}/notes",
        json={"notes": "Followed up via DM"},
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Followed up via DM"


@pytest.mark.asyncio
async def test_bulk_status_update(client: AsyncClient, sample_campaign):
    cid = str(sample_campaign.id)
    resp = await client.patch(
        "/api/v1/campaigns/bulk-status",
        json={"campaign_ids": [cid], "status": "replied"},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] == 1
