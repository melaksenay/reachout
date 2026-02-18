# app/db/session.py
from sqlmodel import create_engine, Session
from app.core.config import get_settings

settings = get_settings()

# create_engine establishes the connection pool to PostgreSQL
engine = create_engine(settings.DATABASE_URL, echo=True)

def get_db():
    """Provides a synchronous database session for a single request."""
    with Session(engine) as session:
        yield session