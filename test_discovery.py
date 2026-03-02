# test_discovery.py
import asyncio
import os
from app.services.discovery import TikTokDiscovery

async def main():
    # 1. Initialize the service
    discovery = TikTokDiscovery()
    

    query = "healthy lifestyle"
    print(f"🚀 Starting TikTok discovery for: '{query}'...")

    try:
        # 2. Run the search logic
        results = await discovery.search_profiles(query)

        if not results:
            print("❌ No leads found. Ensure you've run setup_session.py first!")
            return

        # 3. Display the cleaned results
        print(f"\n✅ Found {len(results)} leads (filtered self):")
        print("-" * 50)
        
        for i, lead in enumerate(results, 1):
            print(f"{i}. @{lead.handle}")
            print(f"   📝 Bio: {lead.bio_text or ''}")
            print(f"   🔗 URL: {lead.url}")
            print("-" * 50)

    except Exception as e:
        print(f"⚠️  Test failed with error: {e}")

if __name__ == "__main__":
    # Safety check for the session folder
    if not os.path.exists("./tiktok_sessions"):
        print("🛑 ERROR: ./tiktok_sessions folder not found.")
        print("Run your setup_session.py script and log in manually first!")
    else:
        asyncio.run(main())