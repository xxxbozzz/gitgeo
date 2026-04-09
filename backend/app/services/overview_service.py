"""Overview service."""

from __future__ import annotations

from typing import Any

from backend.app.db.mysql import database
from backend.app.schemas.articles import ArticleSummaryItem
from backend.app.schemas.overview import (
    LatestArticlesPayload,
    OverviewBoardPayload,
    OverviewKpisPayload,
    OverviewTrendPayload,
    OverviewTrendPoint,
    PendingKeywordItem,
)


def _map_article_summary(row: dict[str, Any]) -> ArticleSummaryItem:
    return ArticleSummaryItem(
        id=int(row["id"]),
        title=str(row["title"]),
        slug=str(row["slug"]),
        quality_score=int(row.get("quality_score") or 0),
        publish_status=int(row.get("publish_status") or 0),
        dim_subject=row.get("dim_subject"),
        dim_action=row.get("dim_action"),
        dim_attribute=row.get("dim_attribute"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


class OverviewService:
    """Read-only overview queries for dashboard KPIs."""

    def get_kpis(self) -> OverviewKpisPayload:
        try:
            avg_score = database.fetch_value(
                "SELECT ROUND(AVG(quality_score), 1) AS value FROM geo_articles WHERE quality_score > 0",
                default=None,
            )
            return OverviewKpisPayload(
                articles_total=int(
                    database.fetch_value(
                        "SELECT COUNT(*) AS value FROM geo_articles",
                        default=0,
                    )
                    or 0
                ),
                passed_articles=int(
                    database.fetch_value(
                        "SELECT COUNT(*) AS value FROM geo_articles WHERE publish_status >= 1",
                        default=0,
                    )
                    or 0
                ),
                pending_keywords=int(
                    database.fetch_value(
                        "SELECT COUNT(*) AS value FROM geo_keywords WHERE target_article_id IS NULL",
                        default=0,
                    )
                    or 0
                ),
                average_quality_score=float(avg_score) if avg_score is not None else None,
                internal_links=int(
                    database.fetch_value(
                        "SELECT COUNT(*) AS value FROM geo_links",
                        default=0,
                    )
                    or 0
                ),
                latest_article_at=database.fetch_value(
                    "SELECT DATE_FORMAT(MAX(created_at), '%Y-%m-%d %H:%i:%s') AS value FROM geo_articles",
                    default=None,
                ),
                warning=None,
            )
        except Exception as exc:
            return OverviewKpisPayload(
                articles_total=0,
                passed_articles=0,
                pending_keywords=0,
                average_quality_score=None,
                internal_links=0,
                latest_article_at=None,
                warning=f"overview_unavailable: {exc}",
            )

    def get_trend(self, *, days: int) -> OverviewTrendPayload:
        try:
            rows = database.fetch_all(
                """
                SELECT DATE(created_at) AS day, COUNT(*) AS count
                FROM geo_articles
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY day
                """,
                params=(days,),
            )
            return OverviewTrendPayload(
                days=days,
                items=[
                    OverviewTrendPoint(day=row.get("day"), count=int(row.get("count") or 0))
                    for row in rows
                ],
                warning=None,
            )
        except Exception as exc:
            return OverviewTrendPayload(days=days, items=[], warning=f"overview_trend_unavailable: {exc}")

    def get_board(self, *, pending_limit: int, article_limit: int) -> OverviewBoardPayload:
        try:
            pending_rows = database.fetch_all(
                """
                SELECT id, keyword, search_volume, difficulty
                FROM geo_keywords
                WHERE target_article_id IS NULL
                ORDER BY id ASC
                LIMIT %s
                """,
                params=(pending_limit,),
            )
            draft_rows = database.fetch_all(
                """
                SELECT
                    id, title, slug, quality_score, publish_status,
                    dim_subject, dim_action, dim_attribute,
                    created_at, updated_at
                FROM geo_articles
                WHERE publish_status = 0
                ORDER BY created_at DESC
                LIMIT %s
                """,
                params=(article_limit,),
            )
            ready_rows = database.fetch_all(
                """
                SELECT
                    id, title, slug, quality_score, publish_status,
                    dim_subject, dim_action, dim_attribute,
                    created_at, updated_at
                FROM geo_articles
                WHERE publish_status >= 1
                ORDER BY created_at DESC
                LIMIT %s
                """,
                params=(article_limit,),
            )
            return OverviewBoardPayload(
                pending_keywords=[
                    PendingKeywordItem(
                        id=int(row["id"]),
                        keyword=str(row["keyword"]),
                        search_volume=int(row.get("search_volume") or 0),
                        difficulty=int(row.get("difficulty") or 0),
                    )
                    for row in pending_rows
                ],
                draft_articles=[_map_article_summary(row) for row in draft_rows],
                ready_articles=[_map_article_summary(row) for row in ready_rows],
                warning=None,
            )
        except Exception as exc:
            return OverviewBoardPayload(
                pending_keywords=[],
                draft_articles=[],
                ready_articles=[],
                warning=f"overview_board_unavailable: {exc}",
            )

    def get_latest_articles(self, *, limit: int) -> LatestArticlesPayload:
        try:
            rows = database.fetch_all(
                """
                SELECT
                    id, title, slug, quality_score, publish_status,
                    dim_subject, dim_action, dim_attribute,
                    created_at, updated_at
                FROM geo_articles
                ORDER BY created_at DESC
                LIMIT %s
                """,
                params=(limit,),
            )
            return LatestArticlesPayload(
                items=[_map_article_summary(row) for row in rows],
                limit=limit,
                warning=None,
            )
        except Exception as exc:
            return LatestArticlesPayload(
                items=[],
                limit=limit,
                warning=f"latest_articles_unavailable: {exc}",
            )


overview_service = OverviewService()
