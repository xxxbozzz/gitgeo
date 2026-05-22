"""Overview repository — dashboard KPIs."""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Article, Keyword, Link


class OverviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_kpis(self) -> dict:
        total = (await self.session.execute(select(func.count()).select_from(Article))).scalar() or 0
        passed = (await self.session.execute(
            select(func.count()).where(Article.publish_status >= 1)
        )).scalar() or 0
        pending_kw = (await self.session.execute(
            select(func.count()).where(Keyword.target_article_id.is_(None))
        )).scalar() or 0
        avg_score = (await self.session.execute(
            select(func.round(func.avg(Article.quality_score), 1)).where(Article.quality_score > 0)
        )).scalar()
        links = (await self.session.execute(select(func.count()).select_from(Link))).scalar() or 0
        latest = (await self.session.execute(
            select(func.max(Article.created_at))
        )).scalar()

        return {
            "articles_total": int(total),
            "passed_articles": int(passed),
            "pending_keywords": int(pending_kw),
            "average_quality_score": float(avg_score) if avg_score else None,
            "internal_links": int(links),
            "latest_article_at": latest.isoformat() if latest else None,
        }

    async def get_trend(self, *, days: int) -> list[dict]:
        stmt = text(
            "SELECT DATE(created_at) AS day, COUNT(*) AS count "
            "FROM geo_articles "
            "WHERE created_at >= CURRENT_DATE - INTERVAL :days DAY "
            "GROUP BY DATE(created_at) ORDER BY day"
        ).bindparams(days=str(days))
        rows = (await self.session.execute(stmt)).all()
        return [{"day": str(r.day), "count": int(r.count)} for r in rows]

    async def list_drafts(self, *, limit: int = 20) -> list:
        stmt = select(Article).where(Article.publish_status == 0).order_by(
            Article.created_at.desc()
        ).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_ready(self, *, limit: int = 20) -> list:
        stmt = select(Article).where(Article.publish_status >= 1).order_by(
            Article.created_at.desc()
        ).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_latest_articles(self, *, limit: int = 20) -> list:
        stmt = select(Article).order_by(Article.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
