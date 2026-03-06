"""Tests for app/api/endpoints.py routes."""
import pytest
from httpx import AsyncClient

from app.models.influencer import Influencer


@pytest.mark.asyncio
async def test_get_influencers_empty(client: AsyncClient):
    resp = await client.get("/api/v1/influencers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_influencers_returns_data(client: AsyncClient, sample_influencer: Influencer):
    resp = await client.get("/api/v1/influencers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["handle"] == "testcreator"


@pytest.mark.asyncio
async def test_get_influencers_filter_platform(client: AsyncClient, db, sample_influencer):
    # Add an instagram influencer
    inf2 = Influencer(
        platform="instagram",
        handle="instauser",
        url="https://instagram.com/instauser",
    )
    db.add(inf2)
    db.commit()

    resp = await client.get("/api/v1/influencers?platform=tiktok")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["platform"] == "tiktok"


@pytest.mark.asyncio
async def test_get_influencers_filter_followers(client: AsyncClient, db, sample_influencer):
    # sample_influencer has 5000 followers
    resp = await client.get("/api/v1/influencers?min_followers=1000&max_followers=10000")
    assert len(resp.json()) == 1

    resp = await client.get("/api/v1/influencers?min_followers=10000")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_bulk_delete(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    resp = await client.post(
        "/api/v1/influencers/bulk-delete",
        json={"influencer_ids": [inf_id]},
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1

    # Verify it's gone
    resp = await client.get("/api/v1/influencers")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_bulk_delete_nonexistent(client: AsyncClient):
    resp = await client.post(
        "/api/v1/influencers/bulk-delete",
        json={"influencer_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


@pytest.mark.asyncio
async def test_bulk_tag_creates_and_links(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    resp = await client.post(
        "/api/v1/influencers/bulk-tag",
        json={"influencer_ids": [inf_id], "tag_name": "vegan"},
    )
    assert resp.status_code == 200
    assert resp.json()["tagged"] == 1

    # Verify tag appears in detail
    detail = await client.get(f"/api/v1/influencers/{inf_id}")
    tags = detail.json()["tags"]
    assert any(t["name"] == "vegan" for t in tags)


@pytest.mark.asyncio
async def test_bulk_tag_idempotent(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    await client.post(
        "/api/v1/influencers/bulk-tag",
        json={"influencer_ids": [inf_id], "tag_name": "fitness"},
    )
    resp = await client.post(
        "/api/v1/influencers/bulk-tag",
        json={"influencer_ids": [inf_id], "tag_name": "fitness"},
    )
    assert resp.json()["tagged"] == 0
