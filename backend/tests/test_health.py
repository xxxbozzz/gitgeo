"""Tests for health check and root endpoints."""

import pytest
from httpx import AsyncClient

needs_db = pytest.mark.skip(reason="Requires PostgreSQL — run with GEO_TEST_DB=1")


@pytest.mark.anyio
async def test_health_returns_200(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_root_returns_200(async_client: AsyncClient):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["service"] is not None


@pytest.mark.anyio
@needs_db
async def test_articles_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/articles?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "items" in data["data"]
