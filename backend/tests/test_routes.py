"""Smoke tests for all registered routes.

All tests run. Without PostgreSQL, data-dependent tests will return 500
(which is expected — no DB). With GEO_TEST_DB=1 and a real PostgreSQL,
all tests pass with 200.
"""

import os
import pytest
from httpx import AsyncClient


_has_db = os.environ.get("GEO_TEST_DB", "").lower() in ("1", "true", "yes")


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


@pytest.mark.anyio
async def test_overview_kpis(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/overview/kpis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_keywords_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/keywords?limit=5")
    if _has_db:
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data["data"]
    else:
        # Without DB, the mock may return 500 — just check route is registered
        assert resp.status_code != 404


@pytest.mark.anyio
async def test_runs_summary(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/runs/summary")
    if _has_db:
        assert resp.status_code == 200
        data = resp.json()
        assert "total_runs" in data["data"]
    else:
        assert resp.status_code != 404


@pytest.mark.anyio
async def test_publications_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/publications?limit=5")
    if _has_db:
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data["data"]
    else:
        assert resp.status_code != 404


@pytest.mark.anyio
async def test_capabilities_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/capabilities?limit=5")
    if _has_db:
        assert resp.status_code == 200
    else:
        assert resp.status_code != 404


@pytest.mark.anyio
async def test_articles_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/articles?limit=5")
    if _has_db:
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "items" in data["data"]
    else:
        assert resp.status_code != 404
