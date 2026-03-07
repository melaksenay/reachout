# app/db/session.py
from sqlmodel import create_engine, Session
from app.core.config import get_settings

settings = get_settings()

# create_engine establishes the connection pool to PostgreSQL.
# Guard against empty URL so tests (which override get_db) can import
# the app without a real DATABASE_URL.
engine = create_engine(settings.DATABASE_URL, echo=True) if settings.DATABASE_URL else None

def get_db():
    """Provides a synchronous database session for a single request."""
    with Session(engine) as session:
        yield session