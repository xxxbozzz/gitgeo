"""Article repository — data access for geo_articles."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Article


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_articles(
        self,
        *,
        status: Optional[str] = None,
        min_score: int = 0,
        query_text: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Article], int]:
        stmt = select(Article)

        if status == "draft":
            stmt = stmt.where(Article.publish_status == 0)
        elif status == "approved":
            stmt = stmt.where(Article.publish_status == 1)
        elif status == "published":
            stmt = stmt.where(Article.publish_status == 2)

        if min_score > 0:
            stmt = stmt.where(Article.quality_score >= min_score)

        if query_text:
            like = f"%{query_text.strip()}%"
            stmt = stmt.where(
                (Article.title.ilike(like)) | (Article.slug.ilike(like))
            )

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Paginate
        stmt = stmt.order_by(Article.created_at.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()

        return list(rows), total

    async def get_by_id(self, article_id: int) -> Optional[Article]:
        return await self.session.get(Article, article_id)

    async def get_by_slug(self, slug: str) -> Optional[Article]:
        stmt = select(Article).where(Article.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def update_score(self, article_id: int, score: int) -> None:
        stmt = update(Article).where(Article.id == article_id).values(quality_score=score)
        await self.session.execute(stmt)

    async def update_status(self, article_id: int, status: int) -> None:
        stmt = update(Article).where(Article.id == article_id).values(publish_status=status)
        await self.session.execute(stmt)

    async def delete(self, article_id: int) -> None:
        stmt = delete(Article).where(Article.id == article_id)
        await self.session.execute(stmt)

    async def status_counts(self) -> dict[str, int]:
        stmt = select(Article.publish_status, func.count()).group_by(Article.publish_status)
        rows = (await self.session.execute(stmt)).all()
        mapping = {0: "draft", 1: "approved", 2: "published", 3: "archived"}
        return {mapping.get(status, str(status)): int(cnt) for status, cnt in rows}
