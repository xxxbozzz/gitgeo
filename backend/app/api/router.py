"""Central API router."""

from fastapi import APIRouter

from backend.app.api.routes import (
    articles,
    capabilities,
    health,
    keywords,
    overview,
    publications,
    runs,
    system,
)


api_router = APIRouter()
api_router.include_router(articles.router)
api_router.include_router(capabilities.router)
api_router.include_router(health.router)
api_router.include_router(keywords.router)
api_router.include_router(overview.router)
api_router.include_router(publications.router)
api_router.include_router(runs.router)
api_router.include_router(system.router)
