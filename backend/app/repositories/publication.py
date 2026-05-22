"""Publication repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ArticlePublication, Article


class PublicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_publications(
        self, *, article_id: Optional[int] = None, platform: Optional[str] = None,
        status: Optional[str] = None, trigger_mode: Optional[str] = None,
        query_text: Optional[str] = None, limit: int = 20, offset: int = 0,
    ) -> tuple[list[ArticlePublication], int]:
        stmt = select(ArticlePublication).outerjoin(Article, Article.id == ArticlePublication.article_id)

        if article_id is not None:
            stmt = stmt.where(ArticlePublication.article_id == article_id)
        if platform:
            stmt = stmt.where(ArticlePublication.platform == platform)
        if status:
            stmt = stmt.where(ArticlePublication.status == status)
        if trigger_mode:
            stmt = stmt.where(ArticlePublication.trigger_mode == trigger_mode)
        if query_text:
            like = f"%{query_text.strip()}%"
            stmt = stmt.where(
                (Article.title.ilike(like)) | (Article.slug.ilike(like))
                | (ArticlePublication.external_id.ilike(like))
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(ArticlePublication.created_at.desc(), ArticlePublication.id.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def get_by_id(self, publication_id: int) -> Optional[ArticlePublication]:
        return await self.session.get(ArticlePublication, publication_id)

    async def get_article(self, article_id: int) -> Optional[Article]:
        return await self.session.get(Article, article_id)

    async def create_attempt(
        self, *, article_id: int, platform: str, publish_mode: str,
        trigger_mode: str, retry_of: Optional[int], request_payload: dict,
    ) -> tuple[int, int]:
        from sqlalchemy import func as sqla_func
        # Get next attempt_no
        max_attempt = (await self.session.execute(
            select(sqla_func.coalesce(sqla_func.max(ArticlePublication.attempt_no), 0)).where(
                ArticlePublication.article_id == article_id,
                ArticlePublication.platform == platform,
            )
        )).scalar() or 0
        attempt_no = max_attempt + 1

        pub = ArticlePublication(
            article_id=article_id, platform=platform, publish_mode=publish_mode,
            status="pending", trigger_mode=trigger_mode, attempt_no=attempt_no,
            retry_of_publication_id=retry_of, request_payload_json=request_payload,
        )
        self.session.add(pub)
        await self.session.flush()
        return pub.id, attempt_no

    async def update_attempt(
        self, publication_id: int, *, status: str, external_id: Optional[str] = None,
        external_url: Optional[str] = None, message: Optional[str] = None,
        error_message: Optional[str] = None, response_payload: Optional[dict] = None,
        published: bool = False,
    ) -> None:
        pub = await self.session.get(ArticlePublication, publication_id)
        if pub is None:
            return
        pub.status = status
        pub.external_id = external_id
        pub.external_url = external_url
        pub.message = message
        pub.error_message = error_message
        pub.response_payload_json = response_payload
        if published:
            from datetime import datetime, timezone
            pub.published_at = datetime.now(timezone.utc)

    async def mark_article_published(self, article_id: int) -> None:
        article = await self.session.get(Article, article_id)
        if article:
            article.publish_status = 2
