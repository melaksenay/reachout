# app/services/ai_outreach.py
import anthropic
from anthropic.types import TextBlock
from app.core.config import get_settings
from app.models.influencer import Influencer


class AIOutreachService:
    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate_message(
        self,
        influencer: Influencer,
        brand_description: str,
        profile_context: dict,
    ) -> str:
        bio = profile_context.get("bio") or "Not available"
        videos = profile_context.get("recent_videos", [])
        video_list = "\n".join(f"- {v}" for v in videos) if videos else "Not available"
        follower_display = (
            f"{influencer.follower_count:,}" if influencer.follower_count else "Unknown"
        )

        prompt = f"""You are writing a personalized outreach DM from a brand to a TikTok creator.

BRAND DESCRIPTION:
{brand_description}

CREATOR PROFILE:
- Handle: @{influencer.handle}
- Followers: {follower_display}
- Bio: {bio}
- Recent video titles:
{video_list}

Write a short, genuine, conversational DM (3-4 sentences max). Do not be generic. Reference something specific from their bio or recent content. End with a low-pressure call to action. Do not use exclamation marks excessively. Return only the message text with no explanation."""

        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        for block in message.content:
            if isinstance(block, TextBlock):
                return block.text.strip()
        return ""
