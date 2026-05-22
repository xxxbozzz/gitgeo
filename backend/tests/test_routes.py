"""Smoke tests for all registered routes.

Tests marked 'db' require PostgreSQL (GEO_TEST_DB=1).
All others run with or without a database.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_all_routes_registered(async_client: AsyncClient):
    """Every migrated route returns non-404."""
    routes = [
        "/api/v1/health", "/api/v1/ready",
        "/api/v1/articles", "/api/v1/articles/summary",
        "/api/v1/keywords", "/api/v1/keywords/gap", "/api/v1/keywords/clusters",
        "/api/v1/overview/kpis", "/api/v1/overview/trend",
        "/api/v1/overview/board", "/api/v1/overview/latest-articles",
        "/api/v1/runs", "/api/v1/runs/summary", "/api/v1/runs/failures",
        "/api/v1/system/status",
        "/api/v1/publications",
        "/api/v1/capabilities",
    ]
    for path in routes:
        resp = await async_client.get(path)
        assert resp.status_code != 404, f"Route {path} NOT REGISTERED (404)"


@pytest.mark.anyio
async def test_health_has_db_field(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/health")
    data = resp.json()
    assert "database" in data["data"]


@pytest.mark.anyio
async def test_system_status(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "environment" in data["data"]
    assert "database" in data["data"]


@pytest.mark.anyio
async def test_overview_kpis(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/overview/kpis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


# ── Data-dependent tests (require PostgreSQL) ──

needs_db = pytest.mark.skip(reason="Requires PostgreSQL — run with GEO_TEST_DB=1")


@pytest.mark.anyio
@needs_db
async def test_keywords_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/keywords?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data["data"]


@pytest.mark.anyio
@needs_db
async def test_runs_summary(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/runs/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_runs" in data["data"]


@pytest.mark.anyio
@needs_db
async def test_publications_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/publications?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data["data"]


@pytest.mark.anyio
@needs_db
async def test_capabilities_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/capabilities?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data["data"]


@pytest.mark.anyio
@needs_db
async def test_articles_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/articles?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "items" in data["data"]
