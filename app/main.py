# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from app.db.session import engine

# You MUST import your models here so SQLModel knows about them before create_all()
from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign

from app.api.endpoints import router as discovery_router
from app.api.campaigns import router as campaign_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created or verified successfully.")
    
    yield  # This is where the app runs
    
    

app = FastAPI(title="Micro-Influencer Outreach Manager", lifespan=lifespan)

app.include_router(discovery_router, prefix="/api/v1")
app.include_router(campaign_router, prefix="/api/v1")