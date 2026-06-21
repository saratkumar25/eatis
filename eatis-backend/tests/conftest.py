"""
tests/conftest.py
───────────────────
Shared pytest fixtures: in-memory SQLite test DB + FastAPI TestClient.

Note: SQLite is used for fast unit testing of API contracts only.
Integration tests against real PostgreSQL should run via docker-compose
in CI (see README "Testing" section).
"""

import os

# Point the app's global DB engine at a local SQLite file BEFORE importing
# app.main — this prevents the lifespan startup hook from trying to reach
# the production Postgres host ("db") which doesn't exist in the test env.
os.environ["DATABASE_URL"] = "sqlite:///./test_eatis.db"
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "test-key-not-used")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
