"""Publication audit and channel-adapter publishing service."""

from __future__ import annotations

import json
import os
from typing import Any

from backend.app.core.settings import get_settings
from backend.app.db.mysql import database
from backend.app.schemas.publications import (
    PublicationDetailItem,
    PublicationDetailPayload,
    PublicationListPayload,
    PublicationSummaryItem,
)
from core.wechat_publisher import WeChatPublisher
from core.zhihu_publisher import ZhihuPublisher


VALID_PUBLICATION_STATUSES = {"pending", "draft_saved", "published", "failed"}
SUCCESSFUL_AUDIT_STATUSES = {"draft_saved", "published"}
CHANNEL_ADAPTERS = {
    "longform_channel": {
        "channel_key": "longform_channel",
        "channel_label": "Longform Channel",
        "adapter_key": "zhihu",
        "adapter_label": "Zhihu Adapter",
    },
    "mobile_channel": {
        "channel_key": "mobile_channel",
        "channel_label": "Mobile Channel",
        "adapter_key": "wechat",
        "adapter_label": "WeChat Adapter",
    },
}
ADAPTER_TO_CHANNEL = {
    item["adapter_key"]: item
    for item in CHANNEL_ADAPTERS.values()
}


def _json_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


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


def _normalize_channel_or_adapter(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).strip().lower()
    if normalized in CHANNEL_ADAPTERS:
        return str(CHANNEL_ADAPTERS[normalized]["adapter_key"])
    if normalized in ADAPTER_TO_CHANNEL:
        return normalized
    return None


def _channel_metadata(adapter_key: str) -> dict[str, str]:
    return ADAPTER_TO_CHANNEL.get(
        adapter_key,
        {
            "channel_key": adapter_key,
            "channel_label": adapter_key,
            "adapter_key": adapter_key,
            "adapter_label": adapter_key,
        },
    )


def _is_retryable_status(*, status: str, publish_mode: str, adapter_key: str) -> bool:
    if adapter_key not in ADAPTER_TO_CHANNEL:
        return False
    if status == "failed":
        return True
    if status == "draft_saved" and publish_mode == "live":
        return True
    return False


def _map_publication_summary(row: dict[str, Any]) -> PublicationSummaryItem:
    publish_mode = str(row["publish_mode"])
    status = str(row["status"])
    adapter_key = str(row["platform"])
    channel_meta = _channel_metadata(adapter_key)
    return PublicationSummaryItem(
        id=int(row["id"]),
        article_id=int(row["article_id"]),
        article_title=row.get("article_title"),
        article_slug=row.get("article_slug"),
        article_publish_status=(
            int(row["article_publish_status"])
            if row.get("article_publish_status") is not None
            else None
        ),
        channel_key=channel_meta["channel_key"],
        channel_label=channel_meta["channel_label"],
        adapter_key=channel_meta["adapter_key"],
        adapter_label=channel_meta["adapter_label"],
        publish_mode=publish_mode,
        status=status,
        trigger_mode=str(row["trigger_mode"]),
        attempt_no=int(row.get("attempt_no") or 1),
        retry_of_publication_id=(
            int(row["retry_of_publication_id"])
            if row.get("retry_of_publication_id") is not None
            else None
        ),
        retryable=_is_retryable_status(
            status=status,
            publish_mode=publish_mode,
            adapter_key=adapter_key,
        ),
        external_id=row.get("external_id"),
        external_url=row.get("external_url"),
        message=row.get("message"),
        error_message=row.get("error_message"),
        published_at=row.get("published_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _map_publication_detail(
    row: dict[str, Any],
    *,
    retry_attempts_total: int,
) -> PublicationDetailItem:
    summary = _map_publication_summary(row)
    return PublicationDetailItem(
        **summary.model_dump(),
        request_payload_json=_decode_json(row.get("request_payload_json")),
        response_payload_json=_decode_json(row.get("response_payload_json")),
        retry_attempts_total=retry_attempts_total,
    )


class PublicationsService:
    """Manage publication attempts, audit rows, and retry lineage."""

    base_publication_sql = """
        SELECT
            p.id, p.article_id,
            a.title AS article_title,
            a.slug AS article_slug,
            a.publish_status AS article_publish_status,
            p.platform, p.publish_mode, p.status, p.trigger_mode,
            p.attempt_no, p.retry_of_publication_id,
            p.external_id, p.external_url,
            p.message, p.error_message,
            p.request_payload_json, p.response_payload_json,
            p.published_at, p.created_at, p.updated_at
        FROM article_publications p
        LEFT JOIN geo_articles a ON a.id = p.article_id
    """

    def _normalize_platform_result(
        self,
        platform_result: dict[str, Any],
        *,
        go_live: bool,
    ) -> tuple[str, str | None, str | None, str, str | None]:
        status = str(
            platform_result.get("status")
            or ("published" if platform_result.get("success") else "failed")
        )
        if status not in VALID_PUBLICATION_STATUSES:
            status = "failed"

        external_id = platform_result.get("external_id")
        if external_id is None and platform_result.get("article_id") is not None:
            external_id = str(platform_result.get("article_id"))
        if external_id is None and platform_result.get("media_id") is not None:
            external_id = str(platform_result.get("media_id"))

        external_url = platform_result.get("external_url") or platform_result.get("url")
        message = str(platform_result.get("message") or "")
        error_message = platform_result.get("error_message")
        if error_message:
            error_message = str(error_message)
        elif go_live and status == "draft_saved":
            error_message = "publish_not_completed"

        return (
            status,
            str(external_id) if external_id is not None else None,
            str(external_url) if external_url else None,
            message,
            error_message,
        )

    def _get_article(self, article_id: int) -> dict[str, Any] | None:
        return database.fetch_one(
            """
            SELECT id, title, slug, content_markdown, publish_status
            FROM geo_articles
            WHERE id = %s
            """,
            params=(article_id,),
        )

    def _get_publication(self, publication_id: int) -> dict[str, Any] | None:
        return database.fetch_one(
            """
            SELECT
                p.id, p.article_id,
                a.title AS article_title,
                a.slug AS article_slug,
                a.publish_status AS article_publish_status,
                p.platform, p.publish_mode, p.status, p.trigger_mode,
                p.attempt_no, p.retry_of_publication_id, p.external_id, p.external_url,
                p.message, p.error_message, p.request_payload_json, p.response_payload_json,
                p.published_at, p.created_at, p.updated_at
            FROM article_publications p
            LEFT JOIN geo_articles a ON a.id = p.article_id
            WHERE p.id = %s
            """,
            params=(publication_id,),
        )

    def _build_list_filters(
        self,
        *,
        article_id: int | None,
        channel: str | None,
        adapter: str | None,
        status: str | None,
        trigger_mode: str | None,
        query_text: str | None,
    ) -> tuple[str, tuple[Any, ...]]:
        clauses: list[str] = []
        params: list[Any] = []

        if article_id is not None:
            clauses.append("p.article_id = %s")
            params.append(article_id)
        normalized_channel = _normalize_channel_or_adapter(channel) or _normalize_channel_or_adapter(adapter)
        if normalized_channel:
            clauses.append("p.platform = %s")
            params.append(normalized_channel)
        if status:
            clauses.append("p.status = %s")
            params.append(status)
        if trigger_mode:
            clauses.append("p.trigger_mode = %s")
            params.append(trigger_mode)
        if query_text:
            like_value = f"%{query_text.strip()}%"
            clauses.append(
                "(a.title LIKE %s OR a.slug LIKE %s OR p.external_id LIKE %s)"
            )
            params.extend([like_value, like_value, like_value])

        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, tuple(params)

    def _is_retryable_row(self, row: dict[str, Any]) -> bool:
        return _is_retryable_status(
            status=str(row.get("status") or ""),
            publish_mode=str(row.get("publish_mode") or ""),
            adapter_key=str(row.get("platform") or ""),
        )

    def _next_attempt_no(self, article_id: int, adapter_key: str) -> int:
        value = database.fetch_value(
            """
            SELECT COALESCE(MAX(attempt_no), 0) + 1 AS value
            FROM article_publications
            WHERE article_id = %s AND platform = %s
            """,
            params=(article_id, adapter_key),
            default=1,
        )
        return int(value or 1)

    def list_publications(
        self,
        *,
        article_id: int | None,
        channel: str | None,
        platform: str | None,
        status: str | None,
        trigger_mode: str | None,
        query_text: str | None,
        limit: int,
        offset: int,
    ) -> PublicationListPayload:
        try:
            where_sql, params = self._build_list_filters(
                article_id=article_id,
                channel=channel,
                adapter=platform,
                status=status,
                trigger_mode=trigger_mode,
                query_text=query_text,
            )
            total = int(
                database.fetch_value(
                    f"SELECT COUNT(*) AS value FROM article_publications p "
                    f"LEFT JOIN geo_articles a ON a.id = p.article_id{where_sql}",
                    params=params,
                    default=0,
                )
                or 0
            )
            rows = database.fetch_all(
                f"{self.base_publication_sql}{where_sql} "
                "ORDER BY p.created_at DESC, p.id DESC LIMIT %s OFFSET %s",
                params=(*params, limit, offset),
            )
            return PublicationListPayload(
                items=[_map_publication_summary(row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
                warning=None,
            )
        except Exception as exc:
            return PublicationListPayload(
                items=[],
                total=0,
                limit=limit,
                offset=offset,
                warning=f"publications_unavailable: {exc}",
            )

    def get_publication_detail(self, publication_id: int) -> PublicationDetailPayload:
        try:
            row = self._get_publication(publication_id)
            if not row:
                return PublicationDetailPayload(
                    publication=None,
                    warning="publication_not_found",
                )

            retry_attempts_total = int(
                database.fetch_value(
                    """
                    SELECT COUNT(*) AS value
                    FROM article_publications
                    WHERE retry_of_publication_id = %s
                    """,
                    params=(publication_id,),
                    default=0,
                )
                or 0
            )
            return PublicationDetailPayload(
                publication=_map_publication_detail(
                    row,
                    retry_attempts_total=retry_attempts_total,
                ),
                warning=None,
            )
        except Exception as exc:
            return PublicationDetailPayload(
                publication=None,
                warning=f"publication_detail_unavailable: {exc}",
            )

    def _create_attempt(
        self,
        *,
        article_id: int,
        adapter_key: str,
        publish_mode: str,
        trigger_mode: str,
        retry_of_publication_id: int | None,
        request_payload: dict[str, Any],
    ) -> tuple[int, int]:
        attempt_no = self._next_attempt_no(article_id, adapter_key)
        with database.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO article_publications
                    (
                        article_id, platform, publish_mode, status, trigger_mode,
                        attempt_no, retry_of_publication_id, request_payload_json
                    )
                    VALUES (%s, %s, %s, 'pending', %s, %s, %s, %s)
                    """,
                    (
                        article_id,
                        adapter_key,
                        publish_mode,
                        trigger_mode,
                        attempt_no,
                        retry_of_publication_id,
                        _json_or_none(request_payload),
                    ),
                )
                conn.commit()
                return int(cursor.lastrowid), attempt_no
            finally:
                cursor.close()

    def _update_attempt(
        self,
        publication_id: int,
        *,
        status: str,
        external_id: str | None,
        external_url: str | None,
        message: str | None,
        error_message: str | None,
        response_payload: dict[str, Any] | None,
    ) -> None:
        if status not in VALID_PUBLICATION_STATUSES:
            raise ValueError(f"invalid_publication_status: {status}")

        with database.connection() as conn:
            cursor = conn.cursor()
            try:
                if status == "published":
                    cursor.execute(
                        """
                        UPDATE article_publications
                        SET status = %s,
                            external_id = %s,
                            external_url = %s,
                            message = %s,
                            error_message = %s,
                            response_payload_json = %s,
                            published_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            status,
                            external_id,
                            external_url,
                            message,
                            error_message,
                            _json_or_none(response_payload),
                            publication_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE article_publications
                        SET status = %s,
                            external_id = %s,
                            external_url = %s,
                            message = %s,
                            error_message = %s,
                            response_payload_json = %s
                        WHERE id = %s
                        """,
                        (
                            status,
                            external_id,
                            external_url,
                            message,
                            error_message,
                            _json_or_none(response_payload),
                            publication_id,
                        ),
                    )
                conn.commit()
            finally:
                cursor.close()

    def _mark_article_published(self, article_id: int) -> None:
        with database.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE geo_articles SET publish_status = 2 WHERE id = %s",
                    (article_id,),
                )
                conn.commit()
            finally:
                cursor.close()

    def _publish_to_adapter(
        self,
        *,
        adapter_key: str,
        title: str,
        content_md: str,
        go_live: bool,
    ) -> dict[str, Any]:
        if adapter_key == "zhihu":
            publisher = ZhihuPublisher()
            if not publisher.ready:
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Cookie 未就绪，请先运行登录脚本",
                    "error_message": "cookie_not_ready",
                }
            return (
                publisher.publish_and_go_live(title, content_md)
                if go_live
                else publisher.publish(title, content_md, topic_tags=["PCB", "电子制造"])
            )

        if adapter_key == "wechat":
            publisher = WeChatPublisher()
            if not publisher.ready:
                return {
                    "success": False,
                    "status": "failed",
                    "message": "AppID/AppSecret 未配置",
                    "error_message": "wechat_credentials_missing",
                }
            return (
                publisher.publish_and_go_live(title, content_md)
                if go_live
                else publisher.publish(title, content_md)
            )

        return {
            "success": False,
            "status": "failed",
            "message": f"不支持的发布适配器: {adapter_key}",
            "error_message": "unsupported_adapter",
        }

    def publish_article(
        self,
        article_id: int,
        *,
        channels: list[str],
        go_live: bool,
        trigger_mode: str = "manual",
        retry_of_publication_id: int | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        os.environ.setdefault(
            "GEO_PUBLISH_REQUEST_TIMEOUT",
            str(settings.publish_request_timeout_seconds),
        )

        article = self._get_article(article_id)
        if not article:
            return {
                "success": False,
                "error_code": "article_not_found",
                "action": "publish",
                "article_id": article_id,
                "message": "未找到该文章。",
            }

        normalized_adapters: list[str] = []
        for item in channels:
            normalized = _normalize_channel_or_adapter(item)
            if normalized and normalized not in normalized_adapters:
                normalized_adapters.append(normalized)
        if not normalized_adapters:
            return {
                "success": False,
                "error_code": "channel_required",
                "action": "publish",
                "article_id": article_id,
                "message": "请至少选择一个发布渠道。",
            }

        if retry_of_publication_id is not None and len(normalized_adapters) != 1:
            return {
                "success": False,
                "error_code": "retry_channel_conflict",
                "action": "publish",
                "article_id": article_id,
                "message": "单次重试只能对应一个渠道。",
            }

        title = str(article.get("title") or "")
        content_md = str(article.get("content_markdown") or "")
        publish_mode = "live" if go_live else "draft"
        results: list[dict[str, Any]] = []

        for adapter_key in normalized_adapters:
            channel_meta = _channel_metadata(adapter_key)
            request_payload = {
                "article_id": article_id,
                "channel_key": channel_meta["channel_key"],
                "adapter_key": adapter_key,
                "publish_mode": publish_mode,
                "trigger_mode": trigger_mode,
                "go_live": go_live,
                "retry_of_publication_id": retry_of_publication_id,
            }
            publication_id, attempt_no = self._create_attempt(
                article_id=article_id,
                adapter_key=adapter_key,
                publish_mode=publish_mode,
                trigger_mode=trigger_mode,
                retry_of_publication_id=retry_of_publication_id,
                request_payload=request_payload,
            )

            try:
                adapter_result = self._publish_to_adapter(
                    adapter_key=adapter_key,
                    title=title,
                    content_md=content_md,
                    go_live=go_live,
                )
            except Exception as exc:
                adapter_result = {
                    "success": False,
                    "status": "failed",
                    "message": f"{adapter_key} 发布异常: {exc}",
                    "error_message": str(exc),
                }

            status, external_id, external_url, message, error_message = self._normalize_platform_result(
                adapter_result,
                go_live=go_live,
            )

            self._update_attempt(
                publication_id,
                status=status,
                external_id=external_id,
                external_url=external_url,
                message=message,
                error_message=error_message,
                response_payload=adapter_result,
            )

            achieved_requested_mode = status == ("published" if go_live else "draft_saved")
            results.append(
                {
                    "publication_id": publication_id,
                    "article_id": article_id,
                    "channel_key": channel_meta["channel_key"],
                    "channel_label": channel_meta["channel_label"],
                    "adapter_key": adapter_key,
                    "adapter_label": channel_meta["adapter_label"],
                    "attempt_no": attempt_no,
                    "retry_of_publication_id": retry_of_publication_id,
                    "publish_mode": publish_mode,
                    "status": status,
                    "success": achieved_requested_mode,
                    "message": message,
                    "error_message": error_message,
                    "external_id": external_id,
                    "external_url": external_url,
                }
            )

        if any(item["status"] in SUCCESSFUL_AUDIT_STATUSES for item in results):
            self._mark_article_published(article_id)

        requested_status = "published" if go_live else "draft_saved"
        any_requested_success = any(item["status"] == requested_status for item in results)
        all_requested_success = bool(results) and all(item["status"] == requested_status for item in results)
        any_audit_success = any(item["status"] in SUCCESSFUL_AUDIT_STATUSES for item in results)
        overall_status = (
            requested_status if all_requested_success
            else "partial" if any_audit_success
            else "failed"
        )

        return {
            "success": any_requested_success,
            "action": "publish",
            "status": overall_status,
            "article_id": article_id,
            "go_live": go_live,
            "trigger_mode": trigger_mode,
            "results": results,
            "message": "发布完成。" if any_requested_success else "渠道发布未达到目标状态。",
        }

    def retry_publication(self, publication_id: int) -> dict[str, Any]:
        row = self._get_publication(publication_id)
        if not row:
            return {
                "success": False,
                "error_code": "publication_not_found",
                "action": "retry_publication",
                "publication_id": publication_id,
                "message": "未找到该发布记录。",
            }

        if not self._is_retryable_row(row):
            return {
                "success": False,
                "error_code": "publication_not_retryable",
                "action": "retry_publication",
                "publication_id": publication_id,
                "message": "该发布记录当前不允许重试。",
            }

        result = self.publish_article(
            int(row["article_id"]),
            channels=[str(row["platform"])],
            go_live=str(row.get("publish_mode") or "draft") == "live",
            trigger_mode="retry",
            retry_of_publication_id=publication_id,
        )
        result["action"] = "retry_publication"
        result["publication_id"] = publication_id
        return result


publications_service = PublicationsService()
