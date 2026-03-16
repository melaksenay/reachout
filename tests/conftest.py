import pytest
import pytest_asyncio
from unittest.mock import patch
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

# Import all models so SQLModel.metadata knows about them
from app.models.influencer import Influencer  # noqa: F401
from app.models.campaign import OutreachCampaign  # noqa: F401
from app.models.influencer_note import InfluencerNote  # noqa: F401
from app.models.tag import Tag, InfluencerTag  # noqa: F401
from app.models.user_settings import UserSettings  # noqa: F401

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.main import app

# Both routers define their own get_scraper — import them so we can override
from app.api.endpoints import get_scraper as endpoints_get_scraper
from app.api.influencer_detail import get_scraper as detail_get_scraper


# ---------------------------------------------------------------------------
# In-memory SQLite engine — StaticPool shares the single connection across
# threads (needed because ASGI transport runs the app in a thread pool).
# ---------------------------------------------------------------------------
test_engine = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def _enable_fk(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """Yield a fresh DB session per test; create tables before, drop after."""
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


class _FakeScraper:
    """Stub that prevents any real browser launches."""
    async def search_profiles(self, query):
        return []
    async def search_by_videos(self, query):
        return []
    async def search_by_hashtag(self, hashtag):
        return []
    async def scrape_profile(self, handle):
        return {"bio": None, "follower_count": None, "recent_videos": []}


@pytest_asyncio.fixture()
async def client(db):
    """Async HTTP client wired to the FastAPI app with test overrides."""

    def _override_db():
        return db

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-id"
    app.dependency_overrides[endpoints_get_scraper] = _FakeScraper
    app.dependency_overrides[detail_get_scraper] = _FakeScraper

    transport = ASGITransport(app=app)
    # Disable Redis in tests so cached endpoints always hit the test DB
    with patch("app.core.cache.get_redis", return_value=None), \
         patch("app.api.endpoints.get_redis", return_value=None), \
         patch("app.api.campaigns.get_redis", return_value=None):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture()
def sample_influencer(db) -> Influencer:
    """Insert and return a sample influencer."""
    inf = Influencer(
        platform="tiktok",
        handle="testcreator",
        url="https://www.tiktok.com/@testcreator",
        bio_text="Test bio",
        follower_count=5000,
    )
    db.add(inf)
    db.commit()
    db.refresh(inf)
    return inf
