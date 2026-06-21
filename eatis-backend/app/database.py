"""
app/database.py
───────────────
SQLAlchemy engine, session factory, and declarative base.
Provides a dependency-injectable DB session for FastAPI routes.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────
_engine_kwargs: dict = {"pool_pre_ping": True, "echo": settings.DEBUG}
_connect_args: dict = {}

if settings.DATABASE_URL.startswith("postgresql"):
    # QueuePool-only options — invalid for SQLite's default pool class
    _engine_kwargs.update(pool_size=10, max_overflow=20)
elif settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)

# ── Session factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Declarative base ───────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


# ── Dependency ─────────────────────────────────────────────────────────────────
def get_db() -> Session:
    """
    FastAPI dependency that yields a DB session and ensures
    it is closed after the request, even on exception.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Health-check helper: returns True if the DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
