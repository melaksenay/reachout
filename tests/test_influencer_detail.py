"""Tests for app/api/influencer_detail.py routes."""
import pytest
from httpx import AsyncClient

from app.models.influencer import Influencer


@pytest.mark.asyncio
async def test_get_detail(client: AsyncClient, sample_influencer: Influencer):
    resp = await client.get(f"/api/v1/influencers/{sample_influencer.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["influencer"]["handle"] == "testcreator"
    assert data["campaigns"] == []
    assert data["notes"] == []
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_get_detail_404(client: AsyncClient):
    resp = await client.get("/api/v1/influencers/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_note(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    resp = await client.post(
        f"/api/v1/influencers/{inf_id}/notes",
        json={"body": "Great engagement rate"},
    )
    assert resp.status_code == 200
    assert resp.json()["body"] == "Great engagement rate"

    # Verify it shows in detail
    detail = await client.get(f"/api/v1/influencers/{inf_id}")
    assert len(detail.json()["notes"]) == 1


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)

    # Add a note
    add_resp = await client.post(
        f"/api/v1/influencers/{inf_id}/notes",
        json={"body": "Temp note"},
    )
    note_id = add_resp.json()["id"]

    # Delete it
    del_resp = await client.delete(f"/api/v1/influencers/{inf_id}/notes/{note_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["ok"] is True

    # Verify it's gone
    detail = await client.get(f"/api/v1/influencers/{inf_id}")
    assert len(detail.json()["notes"]) == 0


@pytest.mark.asyncio
async def test_add_tag(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    resp = await client.post(
        f"/api/v1/influencers/{inf_id}/tags",
        json={"name": "fitness"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "fitness"

    detail = await client.get(f"/api/v1/influencers/{inf_id}")
    assert any(t["name"] == "fitness" for t in detail.json()["tags"])


@pytest.mark.asyncio
async def test_add_tag_idempotent(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    await client.post(f"/api/v1/influencers/{inf_id}/tags", json={"name": "vegan"})
    resp = await client.post(f"/api/v1/influencers/{inf_id}/tags", json={"name": "vegan"})
    assert resp.status_code == 200

    detail = await client.get(f"/api/v1/influencers/{inf_id}")
    vegan_tags = [t for t in detail.json()["tags"] if t["name"] == "vegan"]
    assert len(vegan_tags) == 1


@pytest.mark.asyncio
async def test_remove_tag(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)

    add_resp = await client.post(f"/api/v1/influencers/{inf_id}/tags", json={"name": "remove_me"})
    tag_id = add_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/influencers/{inf_id}/tags/{tag_id}")
    assert del_resp.status_code == 200

    detail = await client.get(f"/api/v1/influencers/{inf_id}")
    assert not any(t["name"] == "remove_me" for t in detail.json()["tags"])


@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient, sample_influencer):
    inf_id = str(sample_influencer.id)
    await client.post(f"/api/v1/influencers/{inf_id}/tags", json={"name": "alpha"})
    await client.post(f"/api/v1/influencers/{inf_id}/tags", json={"name": "beta"})

    resp = await client.get("/api/v1/tags")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()]
    assert "alpha" in names
    assert "beta" in names
