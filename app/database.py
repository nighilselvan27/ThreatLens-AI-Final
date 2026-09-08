"""
SQLAlchemy engine/session setup for the Alert & Notification module.

INTEGRATION NOTE: If the project already has a shared `database.py` /
SQLAlchemy `Base` / session-factory (per the architecture diagram's
PostgreSQL data layer), delete this file and import theirs instead, then
point `app/models/alert.py` at the shared `Base`. This file exists only so
Member 6's module can run and be tested independently before that shared
piece exists.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Call once at startup (or rely on Alembic migrations
    once the team adopts them — see README 'Database Migrations' note)."""
    import app.alerts.models  # noqa: F401  (ensure model is registered)
    Base.metadata.create_all(bind=engine)
