"""Keyword repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Keyword, Article


class KeywordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_keywords(
        self, *, status: Optional[str] = None, query_text: Optional[str] = None,
        limit: int = 20, offset: int = 0,
    ) -> tuple[list[dict], int]:
        stmt = select(
            Keyword.id, Keyword.keyword, Keyword.target_article_id,
            Keyword.search_volume, Keyword.difficulty, Keyword.cannibalization_risk,
            Keyword.created_at,
            Article.title.label("target_article_title"),
            Article.slug.label("target_article_slug"),
        ).outerjoin(Article, Article.id == Keyword.target_article_id)

        if status == "pending":
            stmt = stmt.where(Keyword.target_article_id.is_(None))
        elif status == "consumed":
            stmt = stmt.where(Keyword.target_article_id.isnot(None))

        if query_text:
            like = f"%{query_text.strip()}%"
            stmt = stmt.where(
                (Keyword.keyword.ilike(like))
                | (Article.title.ilike(like))
                | (Article.slug.ilike(like))
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(
            Keyword.target_article_id.is_(None).desc(),
            Keyword.search_volume.desc(),
            Keyword.created_at.desc(),
        ).offset(offset).limit(limit)

        rows = (await self.session.execute(stmt)).all()
        items = [
            {
                "id": r.id, "keyword": r.keyword, "target_article_id": r.target_article_id,
                "target_article_title": r.target_article_title,
                "target_article_slug": r.target_article_slug,
                "search_volume": r.search_volume or 0,
                "difficulty": r.difficulty or 0,
                "cannibalization_risk": bool(r.cannibalization_risk or 0),
            }
            for r in rows
        ]
        return items, total

    async def list_clusters(self, *, limit: int = 50) -> list[dict]:
        stmt = select(
            case(
                (Keyword.target_article_id.is_(None), "待消费关键词"),
                ((Article.dim_subject.is_(None)) | (Article.dim_subject == ""), "已消费/未标注主题"),
                else_=Article.dim_subject,
            ).label("cluster_name"),
            func.count().label("keywords_total"),
            func.sum(case((Keyword.target_article_id.is_(None), 1), else_=0)).label("pending_keywords"),
            func.sum(case((Keyword.target_article_id.isnot(None), 1), else_=0)).label("consumed_keywords"),
            func.round(func.avg(case((Keyword.difficulty > 0, Keyword.difficulty))), 1).label("average_difficulty"),
        ).outerjoin(Article, Article.id == Keyword.target_article_id).group_by("cluster_name").order_by(
            func.count().desc()
        ).limit(limit)

        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "cluster_name": r.cluster_name or "未归类",
                "keywords_total": r.keywords_total or 0,
                "pending_keywords": r.pending_keywords or 0,
                "consumed_keywords": r.consumed_keywords or 0,
                "average_difficulty": float(r.average_difficulty) if r.average_difficulty else None,
            }
            for r in rows
        ]

    async def pending_keywords_count(self) -> int:
        stmt = select(func.count()).where(Keyword.target_article_id.is_(None))
        return (await self.session.execute(stmt)).scalar() or 0

    async def list_pending(self, *, limit: int = 20) -> list[dict]:
        stmt = select(Keyword.id, Keyword.keyword, Keyword.search_volume, Keyword.difficulty).where(
            Keyword.target_article_id.is_(None)
        ).order_by(Keyword.id.asc()).limit(limit)
        rows = (await self.session.execute(stmt)).all()
        return [
            {"id": r.id, "keyword": r.keyword, "search_volume": r.search_volume or 0, "difficulty": r.difficulty or 0}
            for r in rows
        ]
