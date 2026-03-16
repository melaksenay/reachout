# app/main.py
import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from app.db.session import engine

logging.getLogger("app").setLevel(logging.INFO)

# You MUST import your models here so SQLModel knows about them before create_all()
from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign
from app.models.user_settings import UserSettings
from app.models.influencer_note import InfluencerNote
from app.models.tag import Tag, InfluencerTag

from app.api.endpoints import router as discovery_router
from app.api.campaigns import router as campaign_router
from app.api.settings import router as settings_router
from app.api.influencer_detail import router as influencer_detail_router
from app.api.dashboard import router as dashboard_router
from app.services.discovery import TikTokDiscovery
from app.core.cache import get_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created or verified successfully.")

    # Eagerly connect to Redis so we get immediate feedback
    get_redis()

    # Warm up TikTok session in background (refreshes cookies, doesn't save data)
    asyncio.create_task(TikTokDiscovery().warm_up())

    yield  # This is where the app runs
    
    

app = FastAPI(title="Micro-Influencer Outreach Manager", lifespan=lifespan)

app.include_router(discovery_router, prefix="/api/v1")
app.include_router(campaign_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(influencer_detail_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")