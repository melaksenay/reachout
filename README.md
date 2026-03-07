# ReachOut

A full-stack platform for discovering micro-influencers on TikTok and managing outreach campaigns with AI-generated messages.

## Features

- **Influencer Discovery** -- Search TikTok by username, video content, or hashtag to find creators in any niche
- **AI Outreach** -- Generate personalized outreach messages using the Claude API, with one-click editing
- **Campaign Pipeline** -- Kanban board to track outreach status (discovered, drafted, sent, replied, negotiating, closed, rejected)
- **Influencer Management** -- Save, tag, filter, and bulk-manage your influencer list
- **Notes and Tags** -- Add notes and tags to influencers for organization and filtering
- **Profile Refresh** -- Re-scrape TikTok profiles on demand for up-to-date bios and follower counts
- **Authentication** -- Email/password auth via Supabase with JWT-protected API endpoints

## Tech Stack

| Backend | Frontend |
|---|---|
| Python 3.11, FastAPI | React 19, TypeScript |
| SQLModel (ORM) | Vite, Tailwind CSS |
| PostgreSQL (Supabase) | React Router |
| Playwright (stealth scraping) | Supabase Auth |
| Claude API (AI messages) | |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- A Supabase project (for database and auth)
- Anthropic API key (for AI outreach messages)

### Backend

```bash
# Install dependencies
uv sync

# Create .env with required variables
cp .env.example .env  # then fill in values

# Run the server
uvicorn app.main:app --reload
```

Required environment variables: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY`, `MY_HANDLE`

### Frontend

```bash
cd frontend
npm install

# Create .env.local with Supabase credentials
echo "VITE_SUPABASE_URL=your_url" > .env.local
echo "VITE_SUPABASE_PUBLISHABLE_KEY=your_key" >> .env.local

npm run dev
```

The Vite dev server proxies `/api` requests to `localhost:8000`.

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

31 tests covering API endpoints, model validation, service logic, and cascade deletes. Tests use an in-memory SQLite database with mocked auth and scraper -- no external services required.

## CI/CD

GitHub Actions runs on every push to `main` and on pull requests:

- **Backend** -- installs dependencies with `uv`, runs the full test suite
- **Frontend** -- lints with ESLint, builds with TypeScript + Vite
