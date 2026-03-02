import asyncio
import os
from typing import List
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from app.models.influencer import DiscoveredProfile

class TikTokDiscovery:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        # Using the absolute path for your human-verified session
        self.session_path = os.path.abspath("./tiktok_sessions")
        self.my_handle:str|None = os.getenv("MY_HANDLE", "")

    async def warm_up(self) -> None:
        """Visit TikTok to refresh the persistent session cookies.
        Called at server startup — no data is scraped or saved."""
        try:
            async with Stealth().use_async(async_playwright()) as p:
                context = await p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto("https://www.tiktok.com", wait_until="networkidle")
                await context.close()
            print("✅ TikTok session warmed up successfully.")
        except Exception as e:
            print(f"⚠️  TikTok warm-up failed: {e}")

    async def search_profiles(self, query: str) -> List[DiscoveredProfile]:
            leads = []
            async with Stealth().use_async(async_playwright()) as p:
                context = await p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = context.pages[0] if context.pages else await context.new_page()
                
                url = f"https://www.tiktok.com/search/user?q={query.replace(' ', '%20')}"
                await page.goto(url, wait_until="networkidle")

                # Wait for results to actually render
                await page.wait_for_selector('a[href^="/@"]', timeout=15000)

                # Brute force extraction via JS evaluation
                raw_leads = await page.evaluate("""
                    () => {
                        const links = Array.from(document.querySelectorAll('a[href^="/@"]'));
                        return links.map(link => ({
                            handle: link.getAttribute('href').replace('/@', '').split('?')[0],
                            text: link.innerText
                        })).filter(item => item.handle.length > 0);
                    }
                """)

                # Filter out yourself and duplicates
                seen_handles = set()
                for item in raw_leads:
                    handle = item['handle'].strip()
                    
                    # Logic: Skip if it's me, skip if we've already seen it in this list
                    if handle.lower() == self.my_handle or handle in seen_handles:
                        continue
                    
                    seen_handles.add(handle)
                    
                    # 1. Parse the innerText to find metrics
                    text_lines = [line.strip() for line in item['text'].split('\n') if line.strip()]
                    #Follower count is 3rd line.
                    follower_count = text_lines[2] if len(text_lines) > 2 else "No followers provided"
                    
                    leads.append(DiscoveredProfile(
                        platform="tiktok",
                        handle=handle,
                        url=f"https://www.tiktok.com/@{handle}",
                        bio_text=None,  # TikTok doesn't show bios in search results
                        follower_count=self._parse_followers(follower_count)
                    ))

                await context.close()
                    
            return leads

    def _parse_followers(self, follower_str: str) -> int:
        """Simple helper to turn '1.2M' into 1200000"""
        s = follower_str.lower().replace('followers', '').strip()
        try:
            if 'm' in s: return int(float(s.replace('m', '')) * 1_000_000)
            if 'k' in s: return int(float(s.replace('k', '')) * 1_000)
            return int(s)
        except: return 0