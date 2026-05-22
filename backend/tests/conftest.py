"""Shared async test fixtures for gitgeo backend.

Set GEO_TEST_DB=1 to run against a real PostgreSQL instance.
Without it, all tests use MagicMock (works without any database).
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.models import Base
from backend.app.main import create_app


@pytest.fixture(scope="session")
def use_real_db():
    """Only use real DB when explicitly opted in via GEO_TEST_DB=1."""
    return os.environ.get("GEO_TEST_DB", "").lower() in ("1", "true", "yes")


@pytest.fixture
async def real_db_session(use_real_db):
    if not use_real_db:
        yield None
        return

    user = os.environ.get("DB_USER", "geo_app")
    pw = os.environ.get("DB_PASSWORD", "change-this-password")
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "geo_engine")
    url = f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{name}"

    engine = create_async_engine(url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()

    await engine.dispose()


@pytest.fixture
def app(use_real_db, real_db_session):
    app = create_app()

    if use_real_db and real_db_session is not None:
        async def override_get_db():
            yield real_db_session
    else:
        mock_session, _, _ = _make_mock_session()
        async def override_get_db():
            yield mock_session

    from backend.app.core import dependencies
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.state._use_real_db = use_real_db
    return app


@pytest.fixture
async def async_client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def is_real_db(app) -> bool:
    return getattr(app.state, "_use_real_db", False)


# ── Mock helpers ──

def _make_mock_session():
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    class MockScalar:
        def __init__(self, value):
            self._value = value
        def scalar(self):
            return self._value
        def scalars(self):
            return _MockScalars(self._value)

    class _MockScalars:
        def __init__(self, value):
            self._value = value if isinstance(value, list) else ([value] if value is not None else [])
        def all(self):
            return self._value
        def first(self):
            return self._value[0] if self._value else None

    session.execute = AsyncMock(return_value=MockScalar(0))
    session.get = AsyncMock(return_value=None)
    return session, MockScalar, _MockScalars
