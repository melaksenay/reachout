# ReachOut

A full-stack platform for discovering micro-influencers on TikTok and managing outreach campaigns with AI-generated messages.

## Features

- **Influencer Discovery** -- Search TikTok by username, video content, or hashtag to find creators in any niche
- **AI Outreach** -- Generate personalized outreach messages using the Claude API, with one-click editing
- **Campaign Pipeline** -- Kanban board to track outreach status (drafted, sent, replied, negotiating, closed, rejected)
- **Influencer Management** -- Save, tag, filter, and bulk-manage your influencer list
- **Notes and Tags** -- Add notes and tags to influencers for organization and filtering
- **Profile Refresh** -- Re-scrape TikTok profiles on demand for up-to-date bios and follower counts
- **Authentication** -- Email/password auth via Supabase with JWT-protected API endpoints
- **Redis Caching** -- Cache-aside layer with per-endpoint TTLs and automatic invalidation on writes; gracefully degrades without Redis

## Tech Stack

| Backend | Frontend |
|---|---|
| Python 3.11, FastAPI | React 19, TypeScript |
| SQLModel (ORM) | Vite, Tailwind CSS |
| PostgreSQL (Supabase) | React Router |
| Redis (caching) | Supabase Auth |
| Playwright (stealth scraping) | |
| Claude API (AI messages) | |

## Getting Started

### Option A: Docker (recommended)

Runs all four services (Postgres, Redis, backend, frontend) with one command. No local Python or Node setup required.

```bash
cp .env.example .env  # fill in Supabase + Anthropic keys
docker compose up --build
```

Open `http://localhost:3000`.

### Option B: Local dev

**Prerequisites:** Python 3.11+, Node.js 20+, [uv](https://docs.astral.sh/uv/), a Supabase project, Anthropic API key.

```bash
# Backend
uv sync
cp .env.example .env  # fill in values
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
# Create frontend/.env.local with VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY
npm run dev
```

Backend runs at `localhost:8000`, frontend at `localhost:5173` (Vite proxies `/api` to the backend).

### Environment Variables

**Backend (`.env`):** `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY`, `MY_HANDLE`

Optional: `REDIS_URL` (e.g. `redis://localhost:6379`) — enables caching layer.

**Frontend (`frontend/.env.local`):** `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`

## API Overview

| Category | Endpoints |
|---|---|
| Discovery | `POST /api/v1/discover` -- search by user, video, or hashtag |
| Influencers | `GET /api/v1/influencers`, detail view, refresh, bulk delete, bulk tag |
| Campaigns | Draft, status updates, message editing, bulk operations |
| Notes/Tags | CRUD for per-influencer notes and tags |
| AI Messages | `POST /api/v1/generate-message/{campaign_id}` |
| Dashboard | `GET /api/v1/dashboard` -- stats and recent activity |

## Testing

```bash
pytest tests/ -v
```

39 tests covering API endpoints, model validation, service logic, cache behavior, and cascade deletes. Tests use an in-memory SQLite database with mocked auth, scraper, and Redis -- no external services required.

## CI/CD

GitHub Actions runs on every push to `main` and on pull requests:

- **Backend** -- installs dependencies with `uv`, runs the full test suite
- **Frontend** -- lints with ESLint, builds with TypeScript + Vite
