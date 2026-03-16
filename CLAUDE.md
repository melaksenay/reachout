# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Make sure to checkout a branch when adding a new feature. Merge when finished with feature.

## Development Commands

**Run the FastAPI server:**

```bash
uvicorn app.main:app --reload
```

**TikTok session setup (one-time manual browser login):**

```bash
python tiktok_sessions/setup_sesssion.py
```

**Run the React frontend:**

```bash
cd frontend && npm run dev    # Vite dev server at localhost:5173
```

**Run backend tests:**

```bash
pytest tests/ -v
```

## Architecture

### Backend

Layered FastAPI monolith for influencer discovery and outreach. On startup, `TikTokDiscovery.warm_up()` runs as a background task to refresh TikTok session cookies.

- **`app/main.py`** — App factory with lifespan handler (auto-creates tables via SQLModel at startup). Mounts routers at `/api/v1`.
- **`app/api/`** — Route handlers. Use `Depends()` for DB session and service injection.
- **`app/services/`** — Business logic. `TikTokDiscovery` does Playwright-based TikTok scraping with stealth (user/video/hashtag search modes); `OutreachService` generates AI outreach messages via Claude API.
- **`app/models/`** — SQLModel classes (dual ORM table definitions + Pydantic response models).
- **`app/core/config.py`** — Pydantic Settings singleton (loaded from `.env` via `lru_cache`).
- **`app/core/cache.py`** — Redis cache-aside layer. Provides `get_redis()` client, `@cached` decorator, `invalidate_cache()` helper, and a custom JSON encoder for SQLModel/Pydantic objects.
- **`app/db/session.py`** — Synchronous SQLModel/SQLAlchemy engine and `get_db()` generator for request-scoped sessions.

### API Routes

| Method | Path                                               | Description                                                     |
| ------ | -------------------------------------------------- | --------------------------------------------------------------- |
| GET    | `/api/v1/influencers`                            | List saved influencers (filterable by platform, followers, tag) |
| GET    | `/api/v1/influencers/{id}`                       | Influencer detail (profile, campaigns, notes, tags)             |
| POST   | `/api/v1/influencers/{id}/refresh`               | Re-scrape TikTok profile for bio & follower count               |
| POST   | `/api/v1/influencers/{id}/notes`                 | Add a note to an influencer                                     |
| POST   | `/api/v1/influencers/{id}/tags`                  | Add a tag to an influencer                                      |
| DELETE | `/api/v1/influencers/{id}/tags/{tag_id}`         | Remove a tag from an influencer                                 |
| POST   | `/api/v1/influencers/bulk-delete`                | Bulk delete influencers (cascades campaigns, notes, tags)       |
| POST   | `/api/v1/influencers/bulk-tag`                   | Bulk tag influencers                                            |
| POST   | `/api/v1/discover?niche=&platform=&search_type=` | Discover influencers (search_type: user, video, hashtag)        |
| POST   | `/api/v1/campaigns/{influencer_id}/draft`        | Create outreach campaign draft (requires brand_description set) |
| PATCH  | `/api/v1/campaigns/{id}/status`                  | Update campaign status (Kanban board)                           |
| PATCH  | `/api/v1/campaigns/{id}/message`                 | Update AI-generated outreach message                            |
| PATCH  | `/api/v1/campaigns/{id}/notes`                   | Update campaign notes                                           |
| POST   | `/api/v1/campaigns/bulk-draft`                   | Bulk draft campaigns for multiple influencers                   |
| PATCH  | `/api/v1/campaigns/bulk-status`                  | Bulk update campaign statuses                                   |
| GET    | `/api/v1/campaigns`                              | List all campaigns (with influencer data for Kanban)            |
| GET    | `/api/v1/tags`                                   | List all tags                                                   |
| POST   | `/api/v1/generate-message/{campaign_id}`         | Generate AI outreach message via Claude API                     |
| GET    | `/api/v1/dashboard`                              | Analytics: totals, campaigns by status, response rate, recent  |
| GET    | `/api/v1/settings`                               | Get user settings (brand description)                           |
| PATCH  | `/api/v1/settings`                               | Update user settings (brand description)                        |

Route files:

- **`app/api/endpoints.py`** — Discovery, influencer listing, bulk ops, tags, AI message generation.
- **`app/api/campaigns.py`** — Campaign CRUD, draft, bulk-draft, status/message/notes updates.
- **`app/api/influencer_detail.py`** — Single-influencer detail, refresh, notes, tags CRUD.
- **`app/api/dashboard.py`** — Analytics dashboard aggregates.
- **`app/api/settings.py`** — User settings (brand description) read/write.

### Scraping Flow

`TikTokDiscovery` launches a persistent Chromium context (cookies saved in `tiktok_sessions/`) with playwright-stealth. Three discovery modes:

- **User search** (`search_profiles`) — searches `/search/user?q=` for handles/bios
- **Video search** (`search_by_videos`) — searches `/search/video?q=` and extracts creators from video cards
- **Hashtag search** (`search_by_hashtag`) — navigates `/tag/{hashtag}` and extracts creators

Video/hashtag searches extract handles from both embedded JSON (`#__UNIVERSAL_DATA_FOR_REHYDRATION__`) and DOM links (`a[href^="/@"]`), then deduplicate. Follower counts are not available from search results — use the per-influencer refresh endpoint to scrape profile data on demand.

**Important TikTok scraping notes:**

- Use `wait_until="domcontentloaded"` (not `networkidle` — TikTok never stops fetching)
- URL-encode queries with `urllib.parse.quote()` (handles `#` correctly)
- Sequential profile visits trigger captcha sliders — avoid bulk enrichment

## Database

PostgreSQL via Supabase. Tables in `public` schema:

- **`influencer`** — `id` (UUID PK), `platform`, `handle` (unique), `url`, `bio_text`, `follower_count`, `created_at`
- **`outreach_campaign`** — `id` (UUID PK), `influencer_id` (FK → influencer, CASCADE), `status`, `generated_message`, `last_updated`, `status_updated_at`, `notes`
- **`influencer_note`** — `id` (UUID PK), `influencer_id` (FK → influencer, CASCADE), `body`, `created_at`
- **`tag`** — `id` (UUID PK), `name` (unique)
- **`influencer_tag`** — `influencer_id` + `tag_id` (composite PK, both CASCADE)
- **`user_settings`** — `id` (UUID PK), `key` (unique, currently always `"default"`), `brand_description`, `created_at`, `updated_at`

All FKs use `ondelete="CASCADE"` — deleting an influencer cleans up campaigns, notes, and tag links automatically.

Tables are auto-created via SQLModel metadata at startup. Schema changes should be made directly via the Supabase dashboard or SQL editor.

## Caching (Redis)

Cache-aside pattern using Redis with graceful degradation — the app works without Redis (all cache operations are no-ops).

- **`app/core/cache.py`** — Core module. `get_redis()` lazily initializes a Redis client (eagerly called at startup for immediate feedback). `@cached` decorator for simple endpoints; inline cache logic for endpoints with conditional caching.
- Redis is optional: set `REDIS_URL` in `.env` to enable. If unset or Redis is unreachable, the app falls through to the database.

### Cached Endpoints

| Endpoint | Cache Key | TTL | Pattern |
|---|---|---|---|
| `GET /dashboard` | `cache:dashboard` | 60s | `@cached` decorator |
| `GET /tags` | `cache:tags` | 300s | `@cached` decorator |
| `GET /settings` | `cache:settings` | 600s | `@cached` decorator |
| `GET /influencers` (unfiltered) | `cache:influencers` | 30s | Inline (skips cache when filters applied) |
| `GET /campaigns` (unfiltered) | `cache:campaigns` | 60s | Inline (skips cache when status filter applied) |

### Invalidation

Every mutation endpoint calls `invalidate_cache()` with the relevant keys. For example, drafting a campaign invalidates both `"dashboard"` and `"campaigns"`. Tests patch `get_redis` to return `None` so no real Redis is needed.

## Environment Variables

Required in `.env`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `MY_HANDLE` (your TikTok handle, filtered from search results), `ANTHROPIC_API_KEY` (for AI outreach message generation).

Optional: `REDIS_URL` (e.g. `redis://localhost:6379`) — enables Redis caching layer. If unset, caching is disabled and the app queries the database directly.

### Frontend

React + TypeScript + Tailwind CSS app in `frontend/`. Separate `package.json` from root.

- **`frontend/vite.config.ts`** — Vite dev proxy forwards `/api` requests to `localhost:8000` (avoids CORS without backend changes).
- **`frontend/src/lib/supabaseClient.ts`** — Supabase client singleton (auth only, no data queries).
- **`frontend/src/lib/api.ts`** — Typed fetch wrappers for all FastAPI endpoints.
- **`frontend/src/context/AuthContext.tsx`** — Global auth state via Supabase email/password auth.
- **`frontend/src/components/ProtectedRoute.tsx`** — Redirects unauthenticated users to `/login`.
- **`frontend/src/pages/`** — LoginPage, SignUpPage, InfluencersPage (list + bulk actions), InfluencerDetailPage (profile, notes, tags), DiscoverPage (user/video/hashtag search), CampaignsPage (Kanban board).

Frontend env vars in `frontend/.env.local`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` (pointing to remote Supabase).

## Key Dependencies

**Backend:** Python 3.11, FastAPI, SQLModel, psycopg2, Playwright, playwright-stealth, crawlee, pydantic-settings, anthropic (Claude API), redis-py. Package manager: `uv`.

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, @supabase/supabase-js. Package manager: `npm`.

## Campaign Statuses

Valid statuses: `drafted`, `sent`, `replied`, `negotiating`, `closed`, `rejected`. Defined in `app/models/campaign.py:VALID_STATUSES`. Default status for new campaigns is `drafted`.

## Completed Feature Phases

- **P0** — Kanban board for campaign pipeline management
- **P1** — AI-generated outreach messages via Claude API
- **P2** — Influencer detail page with notes and tags
- **P3** — Bulk actions (draft, tag, delete, status update)
- **P4** — JWT auth with Supabase (backend middleware + frontend bearer tokens)
- **P5** — Video & hashtag discovery modes (TikTok content-based search)
- **P6** — Dashboard / analytics
- **P7** — Redis caching layer (cache-aside with graceful degradation)
