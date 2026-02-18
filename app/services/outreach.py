# app/services/outreach.py
from app.models.influencer import Influencer
from app.models.campaign import OutreachCampaign

class OutreachService:
    def create_initial_draft(self, influencer: Influencer) -> str:
        """Creates a standardized template for manual refinement."""
        return (
            f"Hi {influencer.handle},\n\n"
            f"I found your profile on {influencer.platform} and really liked your "
            f"focus on content.\n\n"
            "I'm reaching out because I think your audience would love our "
            "vegan teff crackers. Would you be open to a collaboration?\n\n"
            "Best,\n[Your Name]"
        )