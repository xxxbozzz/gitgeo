"""Keyword read service."""

from __future__ import annotations

from typing import Any

from backend.app.db.mysql import database
from backend.app.schemas.keywords import (
    KeywordClusterItem,
    KeywordClustersPayload,
    KeywordListPayload,
    KeywordSummaryItem,
)


def _map_keyword(row: dict[str, Any]) -> KeywordSummaryItem:
    target_article_id = row.get("target_article_id")
    return KeywordSummaryItem(
        id=int(row["id"]),
        keyword=str(row["keyword"]),
        target_article_id=int(target_article_id) if target_article_id is not None else None,
        target_article_title=row.get("target_article_title"),
        target_article_slug=row.get("target_article_slug"),
        search_volume=int(row.get("search_volume") or 0),
        difficulty=int(row.get("difficulty") or 0),
        cannibalization_risk=bool(row.get("cannibalization_risk") or 0),
        status="consumed" if target_article_id is not None else "pending",
        created_at=row.get("created_at"),
    )


class KeywordsService:
    """Read-only keyword center service."""

    base_sql = """
        SELECT
            k.id,
            k.keyword,
            k.target_article_id,
            k.search_volume,
            k.difficulty,
            k.cannibalization_risk,
            k.created_at,
            a.title AS target_article_title,
            a.slug AS target_article_slug,
            a.dim_subject AS target_article_subject
        FROM geo_keywords k
        LEFT JOIN geo_articles a ON a.id = k.target_article_id
    """

    def _build_filters(
        self,
        *,
        status: str | None,
        query_text: str | None,
    ) -> tuple[str, tuple[Any, ...]]:
        clauses: list[str] = []
        params: list[Any] = []

        if status == "pending":
            clauses.append("k.target_article_id IS NULL")
        elif status == "consumed":
            clauses.append("k.target_article_id IS NOT NULL")

        if query_text:
            like_value = f"%{query_text.strip()}%"
            clauses.append(
                "(k.keyword LIKE %s OR a.title LIKE %s OR a.slug LIKE %s)"
            )
            params.extend([like_value, like_value, like_value])

        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, tuple(params)

    def list_keywords(
        self,
        *,
        status: str | None,
        query_text: str | None,
        limit: int,
        offset: int,
    ) -> KeywordListPayload:
        try:
            where_sql, params = self._build_filters(
                status=status,
                query_text=query_text,
            )
            total = int(
                database.fetch_value(
                    f"SELECT COUNT(*) AS value FROM geo_keywords k "
                    f"LEFT JOIN geo_articles a ON a.id = k.target_article_id{where_sql}",
                    params=params,
                    default=0,
                )
                or 0
            )
            rows = database.fetch_all(
                f"{self.base_sql}{where_sql} "
                "ORDER BY (k.target_article_id IS NULL) DESC, k.search_volume DESC, k.created_at DESC "
                "LIMIT %s OFFSET %s",
                params=(*params, limit, offset),
            )
            return KeywordListPayload(
                items=[_map_keyword(row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
                warning=None,
            )
        except Exception as exc:
            return KeywordListPayload(
                items=[],
                total=0,
                limit=limit,
                offset=offset,
                warning=f"keywords_unavailable: {exc}",
            )

    def list_gap_keywords(
        self,
        *,
        query_text: str | None,
        limit: int,
        offset: int,
    ) -> KeywordListPayload:
        try:
            where_sql, params = self._build_filters(
                status="pending",
                query_text=query_text,
            )
            total = int(
                database.fetch_value(
                    f"SELECT COUNT(*) AS value FROM geo_keywords k "
                    f"LEFT JOIN geo_articles a ON a.id = k.target_article_id{where_sql}",
                    params=params,
                    default=0,
                )
                or 0
            )
            rows = database.fetch_all(
                f"{self.base_sql}{where_sql} "
                "ORDER BY k.search_volume DESC, k.difficulty ASC, k.created_at DESC "
                "LIMIT %s OFFSET %s",
                params=(*params, limit, offset),
            )
            return KeywordListPayload(
                items=[_map_keyword(row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
                warning=None,
            )
        except Exception as exc:
            return KeywordListPayload(
                items=[],
                total=0,
                limit=limit,
                offset=offset,
                warning=f"gap_keywords_unavailable: {exc}",
            )

    def list_clusters(self, *, limit: int) -> KeywordClustersPayload:
        try:
            rows = database.fetch_all(
                """
                SELECT
                    CASE
                        WHEN k.target_article_id IS NULL THEN '待消费关键词'
                        WHEN a.dim_subject IS NULL OR a.dim_subject = '' THEN '已消费/未标注主题'
                        ELSE a.dim_subject
                    END AS cluster_name,
                    COUNT(*) AS keywords_total,
                    SUM(CASE WHEN k.target_article_id IS NULL THEN 1 ELSE 0 END) AS pending_keywords,
                    SUM(CASE WHEN k.target_article_id IS NOT NULL THEN 1 ELSE 0 END) AS consumed_keywords,
                    ROUND(AVG(CASE WHEN k.difficulty > 0 THEN k.difficulty END), 1) AS average_difficulty
                FROM geo_keywords k
                LEFT JOIN geo_articles a ON a.id = k.target_article_id
                GROUP BY cluster_name
                ORDER BY keywords_total DESC, cluster_name ASC
                LIMIT %s
                """,
                params=(limit,),
            )
            return KeywordClustersPayload(
                items=[
                    KeywordClusterItem(
                        cluster_name=str(row.get("cluster_name") or "未归类"),
                        keywords_total=int(row.get("keywords_total") or 0),
                        pending_keywords=int(row.get("pending_keywords") or 0),
                        consumed_keywords=int(row.get("consumed_keywords") or 0),
                        average_difficulty=(
                            float(row["average_difficulty"])
                            if row.get("average_difficulty") is not None
                            else None
                        ),
                    )
                    for row in rows
                ],
                limit=limit,
                warning=None,
            )
        except Exception as exc:
            return KeywordClustersPayload(
                items=[],
                limit=limit,
                warning=f"keyword_clusters_unavailable: {exc}",
            )


keywords_service = KeywordsService()
