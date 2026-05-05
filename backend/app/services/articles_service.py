"""Article read service."""

from __future__ import annotations

import json
import os
import hashlib
from typing import Any

from langchain_openai import ChatOpenAI

from backend.app.core.settings import get_settings
from backend.app.db.mysql import database
from backend.app.schemas.articles import (
    ArticleDetailItem,
    ArticleDetailPayload,
    ArticleListPayload,
    ArticleSummaryItem,
    ArticleSummaryPayload,
)
from backend.app.services.publications_service import publications_service
from core.auto_fixer import AutoFixer
from core.quality_checker import QualityChecker


def _decode_json(value: Any) -> dict[str, Any] | list[Any] | None:
    if value in (None, "", b""):
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
            if isinstance(loaded, (dict, list)):
                return loaded
        except Exception:
            return None
    return None


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


class ArticlesService:
    """Article query and action service."""

    base_sql = """
        SELECT
            id, title, slug, quality_score, publish_status,
            dim_subject, dim_action, dim_attribute,
            created_at, updated_at
        FROM geo_articles
    """

    def _build_filters(
        self,
        *,
        status: str | None,
        min_score: int,
        query_text: str | None,
    ) -> tuple[str, tuple[Any, ...]]:
        clauses: list[str] = []
        params: list[Any] = []

        if status == "draft":
            clauses.append("publish_status = 0")
        elif status == "approved":
            clauses.append("publish_status = 1")
        elif status == "published":
            clauses.append("publish_status >= 2")

        if min_score > 0:
            clauses.append("quality_score >= %s")
            params.append(min_score)

        if query_text:
            clauses.append("(title LIKE %s OR slug LIKE %s)")
            like_value = f"%{query_text.strip()}%"
            params.extend([like_value, like_value])

        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, tuple(params)

    def list_articles(
        self,
        *,
        status: str | None,
        min_score: int,
        query_text: str | None,
        limit: int,
        offset: int,
    ) -> ArticleListPayload:
        try:
            where_sql, params = self._build_filters(
                status=status,
                min_score=min_score,
                query_text=query_text,
            )
            total = int(
                database.fetch_value(
                    f"SELECT COUNT(*) AS value FROM geo_articles{where_sql}",
                    params=params,
                    default=0,
                )
                or 0
            )
            rows = database.fetch_all(
                f"{self.base_sql}{where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                params=(*params, limit, offset),
            )
            return ArticleListPayload(
                items=[_map_article_summary(row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
                warning=None,
            )
        except Exception as exc:
            return ArticleListPayload(
                items=[],
                total=0,
                limit=limit,
                offset=offset,
                warning=f"articles_unavailable: {exc}",
            )

    def get_summary(self) -> ArticleSummaryPayload:
        try:
            row = database.fetch_one(
                """
                SELECT
                    COUNT(*) AS total_articles,
                    SUM(CASE WHEN publish_status = 0 THEN 1 ELSE 0 END) AS draft_articles,
                    SUM(CASE WHEN publish_status = 1 THEN 1 ELSE 0 END) AS approved_articles,
                    SUM(CASE WHEN publish_status >= 2 THEN 1 ELSE 0 END) AS published_articles,
                    ROUND(AVG(CASE WHEN quality_score > 0 THEN quality_score END), 1) AS average_quality_score
                FROM geo_articles
                """
            ) or {}
            avg_score = row.get("average_quality_score")
            return ArticleSummaryPayload(
                total_articles=int(row.get("total_articles") or 0),
                draft_articles=int(row.get("draft_articles") or 0),
                approved_articles=int(row.get("approved_articles") or 0),
                published_articles=int(row.get("published_articles") or 0),
                average_quality_score=float(avg_score) if avg_score is not None else None,
                warning=None,
            )
        except Exception as exc:
            return ArticleSummaryPayload(
                total_articles=0,
                draft_articles=0,
                approved_articles=0,
                published_articles=0,
                average_quality_score=None,
                warning=f"articles_summary_unavailable: {exc}",
            )

    def get_article_detail(self, article_id: int) -> ArticleDetailPayload:
        try:
            row = database.fetch_one(
                """
                SELECT
                    id, title, slug, meta_json, content_markdown, quality_score, publish_status,
                    dim_subject, dim_action, dim_attribute, created_at, updated_at
                FROM geo_articles
                WHERE id = %s
                """,
                params=(article_id,),
            )
            if not row:
                return ArticleDetailPayload(article=None, warning="article_not_found")

            keywords = database.fetch_all(
                """
                SELECT keyword
                FROM geo_keywords
                WHERE target_article_id = %s
                ORDER BY keyword ASC
                """,
                params=(article_id,),
            )
            link_counts = database.fetch_one(
                """
                SELECT
                    SUM(CASE WHEN source_id = %s THEN 1 ELSE 0 END) AS outgoing_links_count,
                    SUM(CASE WHEN target_id = %s THEN 1 ELSE 0 END) AS incoming_links_count
                FROM geo_links
                WHERE source_id = %s OR target_id = %s
                """,
                params=(article_id, article_id, article_id, article_id),
            ) or {}
            run = database.fetch_one(
                """
                SELECT id, status
                FROM geo_job_runs
                WHERE article_id = %s
                ORDER BY started_at DESC
                LIMIT 1
                """,
                params=(article_id,),
            )
            article = ArticleDetailItem(
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
                meta_json=_decode_json(row.get("meta_json")),
                content_markdown=row.get("content_markdown"),
                target_keywords=[str(item["keyword"]) for item in keywords],
                outgoing_links_count=int(link_counts.get("outgoing_links_count") or 0),
                incoming_links_count=int(link_counts.get("incoming_links_count") or 0),
                related_run_id=int(run["id"]) if run and run.get("id") is not None else None,
                related_run_status=str(run["status"]) if run and run.get("status") is not None else None,
            )
            return ArticleDetailPayload(article=article, warning=None)
        except Exception as exc:
            return ArticleDetailPayload(article=None, warning=f"article_detail_unavailable: {exc}")

    def _get_action_article(self, article_id: int) -> dict[str, Any] | None:
        return database.fetch_one(
            """
            SELECT
                id, title, slug, content_markdown, quality_score, publish_status
            FROM geo_articles
            WHERE id = %s
            """,
            params=(article_id,),
        )

    def _recycle_article_with_keyword(
        self,
        article_id: int,
        *,
        keyword: str,
    ) -> dict[str, Any]:
        with database.connection() as conn:
            previous_autocommit = conn.autocommit
            conn.autocommit = False
            cursor = conn.cursor()
            try:
                if keyword:
                    cursor.execute(
                        "INSERT IGNORE INTO geo_keywords (keyword) VALUES (%s)",
                        (keyword,),
                    )
                cursor.execute(
                    "UPDATE geo_keywords SET target_article_id = NULL WHERE target_article_id = %s",
                    (article_id,),
                )
                cursor.execute(
                    "DELETE FROM geo_links WHERE source_id = %s OR target_id = %s",
                    (article_id, article_id),
                )
                cursor.execute("DELETE FROM geo_articles WHERE id = %s", (article_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
                conn.autocommit = previous_autocommit

        return {
            "success": True,
            "action": "recycle",
            "status": "recycled",
            "article_id": article_id,
            "recycled_keyword": keyword,
            "message": f"已回收关键词「{keyword}」并删除文章 #{article_id}。",
        }

    def refix_article(self, article_id: int) -> dict[str, Any]:
        row = self._get_action_article(article_id)
        if not row:
            return {
                "success": False,
                "error_code": "article_not_found",
                "action": "refix",
                "article_id": article_id,
                "message": "未找到该文章。",
            }

        title = str(row.get("title") or "")
        content = str(row.get("content_markdown") or "")
        checker = QualityChecker()
        fixer = AutoFixer()
        score, report = checker.evaluate_article(title, content)
        fix_prompt = fixer.generate_fix_prompt(content, report)

        if not fix_prompt:
            return {
                "success": True,
                "action": "refix",
                "status": "no_change",
                "article_id": article_id,
                "quality_score": int(score),
                "message": f"文章已通过质检 ({score} 分)，无需修复。",
            }

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            return {
                "success": False,
                "error_code": "llm_api_missing",
                "action": "refix",
                "article_id": article_id,
                "message": "未配置可用的 LLM API Key，无法执行返修。",
            }

        settings = get_settings()
        _model = os.getenv("GEO_LLM_MODEL") or os.getenv("OPENAI_MODEL", "deepseek-chat")
        _base = os.getenv("GEO_LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "https://api.deepseek.com"
        llm = ChatOpenAI(
            model=_model,
            api_key=api_key,
            base_url=_base,
            temperature=0.3,
            timeout=settings.article_action_timeout_seconds,
            max_tokens=settings.llm_fix_max_tokens,
        )
        result = llm.invoke(fix_prompt)
        new_content = result.content if hasattr(result, "content") else str(result)

        if len(new_content.strip()) < 500:
            return {
                "success": False,
                "error_code": "repair_result_too_short",
                "action": "refix",
                "article_id": article_id,
                "message": "返修结果过短，请重试。",
            }

        new_score, _ = checker.evaluate_article(title, new_content)
        if new_score >= checker.PASS_THRESHOLD:
            content_hash = hashlib.md5(new_content.encode("utf-8")).hexdigest()
            with database.connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        UPDATE geo_articles
                        SET content_markdown = %s,
                            content_hash = %s,
                            quality_score = %s,
                            publish_status = 1
                        WHERE id = %s
                        """,
                        (new_content, content_hash, new_score, article_id),
                    )
                    conn.commit()
                finally:
                    cursor.close()

            return {
                "success": True,
                "action": "refix",
                "status": "updated",
                "article_id": article_id,
                "quality_score": int(new_score),
                "publish_status": 1,
                "message": f"修复成功，新质量分 {new_score}。",
            }

        keyword = str(row.get("slug") or "").replace("-", " ").strip()
        recycle_result = self._recycle_article_with_keyword(article_id, keyword=keyword)
        recycle_result.update(
            {
                "action": "refix",
                "quality_score": int(new_score),
                "status": "recycled_after_failed_refix",
                "message": (
                    f"修复后仍仅 {new_score} 分 (<{checker.PASS_THRESHOLD})。"
                    f"已回收关键词「{keyword}」并删除文章，等待重新生成。"
                ),
            }
        )
        return recycle_result

    def recycle_article(self, article_id: int) -> dict[str, Any]:
        row = self._get_action_article(article_id)
        if not row:
            return {
                "success": False,
                "error_code": "article_not_found",
                "action": "recycle",
                "article_id": article_id,
                "message": "未找到该文章。",
            }

        keyword = str(row.get("slug") or "").replace("-", " ").strip()
        return self._recycle_article_with_keyword(article_id, keyword=keyword)

    def publish_article(
        self,
        article_id: int,
        *,
        channels: list[str],
        go_live: bool,
    ) -> dict[str, Any]:
        return publications_service.publish_article(
            article_id,
            channels=channels,
            go_live=go_live,
            trigger_mode="manual",
        )


articles_service = ArticlesService()
