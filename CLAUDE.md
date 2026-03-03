# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**No test framework or linter is currently configured.**

## Architecture

### Backend

Layered FastAPI monolith for influencer discovery and outreach. On startup, `TikTokDiscovery.warm_up()` runs as a background task to refresh TikTok session cookies.

- **`app/main.py`** — App factory with lifespan handler (auto-creates tables via SQLModel at startup). Mounts routers at `/api/v1`.
- **`app/api/`** — Route handlers. Use `Depends()` for DB session and service injection.
- **`app/services/`** — Business logic. `TikTokDiscovery` does Playwright-based TikTok scraping with stealth; `OutreachService` generates templated outreach messages.
- **`app/models/`** — SQLModel classes (dual ORM table definitions + Pydantic response models).
- **`app/core/config.py`** — Pydantic Settings singleton (loaded from `.env` via `lru_cache`).
- **`app/db/session.py`** — Synchronous SQLModel/SQLAlchemy engine and `get_db()` generator for request-scoped sessions.

### API Routes

| Method | Path                                        | Description                            |
| ------ | ------------------------------------------- | -------------------------------------- |
| GET    | `/api/v1/influencers`                     | List saved influencers (newest first)  |
| POST   | `/api/v1/discover?niche=&platform=`       | Scrape TikTok, dedup, save influencers |
| POST   | `/api/v1/campaigns/{influencer_id}/draft` | Create outreach campaign draft         |

### Scraping Flow

`TikTokDiscovery` launches a persistent Chromium context (cookies saved in `tiktok_sessions/`) with playwright-stealth, navigates TikTok search, and extracts handles/follower counts via `page.evaluate()`.

## Database

PostgreSQL via Supabase. Two tables in `public` schema:

- **`influencer`** — `id` (UUID PK), `platform`, `handle` (unique), `url`, `bio_text`, `follower_count`, `created_at`
- **`outreach_campaign`** — `id` (UUID PK), `influencer_id` (FK → influencer), `status` (default 'discovered'), `generated_message`, `last_updated`

Tables are auto-created via SQLModel metadata at startup. Schema changes should be made directly via the Supabase dashboard or SQL editor.

## Environment Variables

Required in `.env`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `MY_HANDLE, ANTHROPIC_API_KEY` (your TikTok handle, 

### Frontend

React + TypeScript + Tailwind CSS app in `frontend/`. Separate `package.json` from root.

- **`frontend/vite.config.ts`** — Vite dev proxy forwards `/api` requests to `localhost:8000` (avoids CORS without backend changes).
- **`frontend/src/lib/supabaseClient.ts`** — Supabase client singleton (auth only, no data queries).
- **`frontend/src/lib/api.ts`** — Typed fetch wrappers for all FastAPI endpoints.
- **`frontend/src/context/AuthContext.tsx`** — Global auth state via Supabase email/password auth.
- **`frontend/src/components/ProtectedRoute.tsx`** — Redirects unauthenticated users to `/login`.
- **`frontend/src/pages/`** — LoginPage, SignUpPage, InfluencersPage, DiscoverPage, CampaignsPage.

Frontend env vars in `frontend/.env.local`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` (pointing to remote Supabase).

## Key Dependencies

**Backend:** Python 3.11, FastAPI, SQLModel, psycopg2, Playwright, playwright-stealth, crawlee, pydantic-settings. Package manager: `uv`.

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, @supabase/supabase-js. Package manager: `npm`.
