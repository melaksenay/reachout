import asyncio
import os
from typing import Dict, List
from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Playwright
from playwright_stealth import Stealth
from app.models.influencer import DiscoveredProfile


class TikTokDiscovery:
    _context: BrowserContext | None = None
    _playwright: Playwright | None = None
    _stealth_cm = None  # Stealth context manager
    _lock = asyncio.Lock()

    def __init__(self):
        load_dotenv()
        self.session_path = os.path.abspath("./tiktok_sessions")
        self.my_handle: str | None = os.getenv("MY_HANDLE", "")

    async def _get_context(self) -> BrowserContext:
        """Lazily create and cache a persistent browser context."""
        async with TikTokDiscovery._lock:
            if TikTokDiscovery._context is not None:
                return TikTokDiscovery._context

            stealth = Stealth()
            TikTokDiscovery._stealth_cm = stealth.use_async(async_playwright())
            TikTokDiscovery._playwright = await TikTokDiscovery._stealth_cm.__aenter__()

            TikTokDiscovery._context = await TikTokDiscovery._playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            return TikTokDiscovery._context

    async def _recreate_context(self) -> None:
        """Close and discard the cached context so the next call creates a fresh one."""
        async with TikTokDiscovery._lock:
            if TikTokDiscovery._context is not None:
                try:
                    await TikTokDiscovery._context.close()
                except Exception:
                    pass
                TikTokDiscovery._context = None
            if TikTokDiscovery._stealth_cm is not None:
                try:
                    await TikTokDiscovery._stealth_cm.__aexit__(None, None, None)
                except Exception:
                    pass
                TikTokDiscovery._stealth_cm = None
                TikTokDiscovery._playwright = None

    async def warm_up(self) -> None:
        """Visit TikTok to refresh the persistent session cookies.
        Called at server startup — no data is scraped or saved."""
        try:
            ctx = await self._get_context()
            page = await ctx.new_page()
            try:
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await page.goto("https://www.tiktok.com/search/user?q=fit", wait_until="networkidle", timeout=30000)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            print(f"⚠️  TikTok warm-up failed after {max_retries} attempts")
                            raise e
                        print(f"Attempt {attempt + 1} failed. Retrying")
            finally:
                await page.close()
            print("✅ TikTok session warmed up successfully.")
        except Exception as e:
            print(f"⚠️  TikTok warm-up failed: {e}")
            await self._recreate_context()

    async def search_profiles(self, query: str) -> List[DiscoveredProfile]:
        leads = []
        try:
            ctx = await self._get_context()
            page = await ctx.new_page()
        except Exception:
            await self._recreate_context()
            ctx = await self._get_context()
            page = await ctx.new_page()

        try:
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

                if handle.lower() == self.my_handle or handle in seen_handles:
                    continue

                seen_handles.add(handle)

                text_lines = [line.strip() for line in item['text'].split('\n') if line.strip()]
                follower_count = text_lines[2] if len(text_lines) > 2 else "No followers provided"

                leads.append(DiscoveredProfile(
                    platform="tiktok",
                    handle=handle,
                    url=f"https://www.tiktok.com/@{handle}",
                    bio_text=None,
                    follower_count=self._parse_followers(follower_count)
                ))
        except Exception as e:
            print(f"Search failed: {e}")
            await self._recreate_context()
        finally:
            await page.close()

        return leads

    async def scrape_profile(self, handle: str) -> Dict:
        """Navigate to an influencer's TikTok profile and extract bio, follower count, and recent video titles."""
        result: Dict = {"bio": None, "follower_count": None, "recent_videos": []}
        try:
            try:
                ctx = await self._get_context()
                page = await ctx.new_page()
            except Exception:
                await self._recreate_context()
                ctx = await self._get_context()
                page = await ctx.new_page()

            try:
                await page.goto(
                    f"https://www.tiktok.com/@{handle}",
                    wait_until="networkidle",
                    timeout=20000
                )

                result["bio"] = await page.evaluate("""
                    () => {
                        const bio = document.querySelector('h2[data-e2e="user-bio"]');
                        if (bio) return bio.innerText;
                        const meta = document.querySelector('meta[name="description"]');
                        return meta ? meta.getAttribute('content') : null;
                    }
                """)

                fc_str = await page.evaluate("""
                    () => {
                        const el = document.querySelector('[data-e2e="followers-count"]');
                        return el ? el.innerText : null;
                    }
                """)
                if fc_str:
                    result["follower_count"] = self._parse_followers(fc_str)

                result["recent_videos"] = await page.evaluate("""
                    () => {
                        const items = Array.from(
                            document.querySelectorAll('div[data-e2e="user-post-item"]')
                        ).slice(0, 6);
                        return items.map(el => {
                            const link = el.querySelector('a');
                            return link ? (link.getAttribute('title') || link.innerText || '').trim() : null;
                        }).filter(Boolean);
                    }
                """)
            finally:
                await page.close()
        except Exception as e:
            print(f"Profile scrape for @{handle} failed: {e}")
            await self._recreate_context()
        return result

    async def _scroll_page(self, page, times: int = 3, delay: int = 2000) -> None:
        """Scroll down the page to trigger infinite scroll loading."""
        for _ in range(times):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(delay)

    async def _extract_creators_from_video_page(self, page) -> List[str]:
        """Extract unique creator handles from a page showing video cards."""
        handles: List[str] = []

        # Extract from embedded JSON
        try:
            json_handles = await page.evaluate("""
                () => {
                    const el = document.querySelector('#__UNIVERSAL_DATA_FOR_REHYDRATION__');
                    if (!el) return [];
                    try {
                        const data = JSON.parse(el.textContent);
                        const handles = [];
                        const walk = (obj) => {
                            if (!obj || typeof obj !== 'object') return;
                            if (obj.uniqueId && typeof obj.uniqueId === 'string') {
                                handles.push(obj.uniqueId);
                            }
                            if (Array.isArray(obj)) {
                                obj.forEach(walk);
                            } else {
                                Object.values(obj).forEach(walk);
                            }
                        };
                        walk(data);
                        return handles;
                    } catch { return []; }
                }
            """)
            handles.extend(json_handles)
        except Exception:
            pass

        # Also extract from DOM links (scrolled content won't be in the rehydration JSON)
        dom_handles = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href^="/@"]'));
                return links.map(l => l.getAttribute('href').replace('/@', '').split('?')[0])
                    .filter(h => h.length > 0);
            }
        """)
        handles.extend(dom_handles)

        # Deduplicate and filter
        seen: set[str] = set()
        unique: List[str] = []
        for h in handles:
            h = h.strip()
            if h and h.lower() != self.my_handle and h not in seen:
                seen.add(h)
                unique.append(h)
        return unique

    def _handles_to_profiles(self, handles: List[str]) -> List[DiscoveredProfile]:
        """Convert a list of handles into DiscoveredProfile objects (without enrichment)."""
        return [
            DiscoveredProfile(
                platform="tiktok",
                handle=h,
                url=f"https://www.tiktok.com/@{h}",
                bio_text=None,
                follower_count=None,
            )
            for h in handles
        ]

    async def search_by_videos(self, query: str) -> List[DiscoveredProfile]:
        """Search TikTok videos by keyword and extract the creators."""
        try:
            ctx = await self._get_context()
            page = await ctx.new_page()
        except Exception:
            await self._recreate_context()
            ctx = await self._get_context()
            page = await ctx.new_page()

        handles: List[str] = []
        try:
            from urllib.parse import quote
            url = f"https://www.tiktok.com/search/video?q={quote(query)}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for video content to render (not networkidle — TikTok never stops fetching)
            await page.wait_for_selector('a[href^="/@"]', timeout=20000)
            await self._scroll_page(page, times=3)
            handles = await self._extract_creators_from_video_page(page)
            print(f"[video search] Extracted {len(handles)} unique handles")
        except Exception as e:
            print(f"Video search failed: {e}")
            await self._recreate_context()
        finally:
            await page.close()

        return self._handles_to_profiles(handles)

    async def search_by_hashtag(self, hashtag: str) -> List[DiscoveredProfile]:
        """Search TikTok by hashtag and extract the creators from trending videos."""
        tag = hashtag.lstrip("#").strip().replace(" ", "")

        try:
            ctx = await self._get_context()
            page = await ctx.new_page()
        except Exception:
            await self._recreate_context()
            ctx = await self._get_context()
            page = await ctx.new_page()

        handles: List[str] = []
        try:
            url = f"https://www.tiktok.com/tag/{tag}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector('a[href^="/@"]', timeout=20000)
            await self._scroll_page(page, times=3)
            handles = await self._extract_creators_from_video_page(page)
        except Exception as e:
            print(f"Hashtag search failed: {e}")
            await self._recreate_context()
        finally:
            await page.close()

        return self._handles_to_profiles(handles)

    def _parse_followers(self, follower_str: str) -> int:
        """Simple helper to turn '1.2M' into 1200000"""
        s = follower_str.lower().replace('followers', '').strip()
        try:
            if 'm' in s: return int(float(s.replace('m', '')) * 1_000_000)
            if 'k' in s: return int(float(s.replace('k', '')) * 1_000)
            return int(s)
        except: return 0
