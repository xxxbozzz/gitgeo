"""FastAPI dependency injection providers."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.repositories.article import ArticleRepository
from backend.app.repositories.capability import CapabilityRepository
from backend.app.repositories.keyword import KeywordRepository
from backend.app.repositories.overview import OverviewRepository
from backend.app.repositories.publication import PublicationRepository
from backend.app.repositories.run import RunRepository
from backend.app.repositories.system import SystemRepository


async def get_article_repo(db: AsyncSession = Depends(get_db)) -> ArticleRepository:
    return ArticleRepository(db)


async def get_capability_repo(db: AsyncSession = Depends(get_db)) -> CapabilityRepository:
    return CapabilityRepository(db)


async def get_keyword_repo(db: AsyncSession = Depends(get_db)) -> KeywordRepository:
    return KeywordRepository(db)


async def get_overview_repo(db: AsyncSession = Depends(get_db)) -> OverviewRepository:
    return OverviewRepository(db)


async def get_publication_repo(db: AsyncSession = Depends(get_db)) -> PublicationRepository:
    return PublicationRepository(db)


async def get_run_repo(db: AsyncSession = Depends(get_db)) -> RunRepository:
    return RunRepository(db)


async def get_system_repo(db: AsyncSession = Depends(get_db)) -> SystemRepository:
    return SystemRepository(db)
