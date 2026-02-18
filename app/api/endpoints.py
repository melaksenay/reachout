from fastapi import APIRouter, Depends
from sqlmodel import Session, select, desc
from typing import List

from app.db.session import get_db
from app.services.discovery import TikTokDiscovery
from app.models.influencer import Influencer

router = APIRouter()

def get_scraper() -> TikTokDiscovery:
    return TikTokDiscovery()


@router.get("/influencers", response_model=List[Influencer])
async def get_all_influencers(db: Session = Depends(get_db)):
    statement = select(Influencer).order_by(desc(Influencer.created_at))
    results = db.exec(statement).all()
    return results

# Setting response_model automatically serializes the output and filters internal fields
@router.post("/discover", response_model=List[Influencer])
async def discover_influencers(
    niche: str, 
    platform: str = "tiktok",
    db: Session = Depends(get_db),
    scraper: TikTokDiscovery = Depends(get_scraper)
):
    
    # 1. Fetch raw dictionaries from the scraper service
    raw_profiles = await scraper.search_profiles(query=niche)
    
    saved_influencers = []
    new_influencers = []
    
    for profile_data in raw_profiles:
        # 2. Execute a SQL SELECT statement to check for existing handles
        statement = select(Influencer).where(Influencer.handle == profile_data["handle"])
        existing_influencer = db.exec(statement).first()
        
        if existing_influencer:
            saved_influencers.append(existing_influencer)
        else:
            # 3. Instantiate the SQLModel class using dictionary unpacking (**profile_data)
            new_influencer = Influencer(**profile_data)
            db.add(new_influencer)
            new_influencers.append(new_influencer)
            saved_influencers.append(new_influencer)
            
    # 4. Commit only if new records were added to the session
    if new_influencers:
        db.commit()
        # 5. Refresh loads the database-generated UUIDs and default values back into the Python objects
        for influencer in new_influencers:
            db.refresh(influencer)
            
    return saved_influencers