"""
SQLAlchemy engine/session for the Alert & Notification Module.

ASSUMPTION / TODO FOR MEMBER 8:
`backend/app/database/` (Member 1's territory) is currently empty, so
there is no shared `Base`/`engine`/`get_db` to import yet. This module
creates its own, pointed at the *same* `DATABASE_URL` every other module
will use, so the `alerts` table lands in the same PostgreSQL database
as everyone else's tables (per the architecture diagram: one PostgreSQL
instance for user/system data).

Once Member 1 publishes a shared `backend/app/database/session.py`
(with a shared `Base` + `get_db`), do this:
  1. Delete this file.
  2. In models.py, change `from app.alerts.database import Base` to
     `from app.database.session import Base`.
  3. In router.py, change the `get_db` import the same way.
  4. Re-run `alembic revision --autogenerate` so the alerts table is
     tracked under the shared metadata instead of this module's own.
No alert business logic needs to change for that migration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.alerts.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
