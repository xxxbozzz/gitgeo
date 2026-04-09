"""Capability center service."""

from __future__ import annotations

import json
from typing import Any

from backend.app.db.mysql import database
from backend.app.schemas.capabilities import (
    CapabilityArticleReference,
    CapabilityDetailItem,
    CapabilityDetailPayload,
    CapabilityListPayload,
    CapabilitySourceItem,
    CapabilitySourcesPayload,
    CapabilitySummaryItem,
)
from core.capability_store import DEFAULT_PROFILE, capability_store


CAPABILITY_PROFILE_CODE = str(DEFAULT_PROFILE.get("profile_code") or "default-capability-profile")


def _decode_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]

    if not value:
        return []

    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []

    if not isinstance(parsed, list):
        return []

    return [str(item) for item in parsed if item]


class CapabilitiesService:
    """Read and lightweight write operations for capability center."""

    def _ensure_seed(self) -> str | None:
        try:
            if capability_store.ensure_seed_data():
                return None
            return "capability_seed_unavailable"
        except Exception as exc:
            return f"capability_seed_unavailable: {exc}"

    def list_capabilities(
        self,
        *,
        active: bool | None,
        group_code: str | None,
        query_text: str | None,
        limit: int,
        offset: int,
    ) -> CapabilityListPayload:
        warning = self._ensure_seed()

        try:
            where_clauses = ["p.profile_code = %s"]
            where_params: list[Any] = [CAPABILITY_PROFILE_CODE]

            if active is not None:
                where_clauses.append("s.is_active = %s")
                where_params.append(1 if active else 0)

            if group_code:
                where_clauses.append("(s.group_code = %s OR s.group_name = %s)")
                where_params.extend([group_code, group_code])

            if query_text:
                like = f"%{query_text.strip()}%"
                where_clauses.append(
                    "("
                    "s.capability_name LIKE %s OR "
                    "s.capability_code LIKE %s OR "
                    "s.public_claim LIKE %s OR "
                    "s.group_name LIKE %s"
                    ")"
                )
                where_params.extend([like, like, like, like])

            where_sql = f"WHERE {' AND '.join(where_clauses)}"
            total = int(
                database.fetch_value(
                    f"""
                    SELECT COUNT(*) AS value
                    FROM geo_capability_specs s
                    JOIN geo_capability_profiles p ON p.id = s.profile_id
                    {where_sql}
                    """,
                    params=tuple(where_params),
                    default=0,
                )
                or 0
            )

            rows = database.fetch_all(
                f"""
                SELECT
                  s.id,
                  s.group_code,
                  s.group_name,
                  s.capability_code,
                  s.capability_name,
                  s.category,
                  s.public_claim,
                  s.claim_level,
                  s.confidence_score,
                  s.is_active,
                  s.application_tags_json,
                  s.updated_at,
                  COUNT(DISTINCT ss.source_id) AS source_count
                FROM geo_capability_specs s
                JOIN geo_capability_profiles p ON p.id = s.profile_id
                LEFT JOIN geo_capability_spec_sources ss ON ss.spec_id = s.id
                {where_sql}
                GROUP BY s.id
                ORDER BY s.is_active DESC, s.group_name ASC, s.capability_name ASC
                LIMIT %s OFFSET %s
                """,
                params=tuple([*where_params, limit, offset]),
            )

            active_total = int(
                database.fetch_value(
                    """
                    SELECT COUNT(*) AS value
                    FROM geo_capability_specs s
                    JOIN geo_capability_profiles p ON p.id = s.profile_id
                    WHERE p.profile_code = %s AND s.is_active = 1
                    """,
                    params=(CAPABILITY_PROFILE_CODE,),
                    default=0,
                )
                or 0
            )
            inactive_total = int(
                database.fetch_value(
                    """
                    SELECT COUNT(*) AS value
                    FROM geo_capability_specs s
                    JOIN geo_capability_profiles p ON p.id = s.profile_id
                    WHERE p.profile_code = %s AND s.is_active = 0
                    """,
                    params=(CAPABILITY_PROFILE_CODE,),
                    default=0,
                )
                or 0
            )
            groups_total = int(
                database.fetch_value(
                    """
                    SELECT COUNT(DISTINCT s.group_code) AS value
                    FROM geo_capability_specs s
                    JOIN geo_capability_profiles p ON p.id = s.profile_id
                    WHERE p.profile_code = %s
                    """,
                    params=(CAPABILITY_PROFILE_CODE,),
                    default=0,
                )
                or 0
            )

            items = [
                CapabilitySummaryItem(
                    id=int(row["id"]),
                    group_code=str(row["group_code"]),
                    group_name=str(row["group_name"]),
                    capability_code=str(row["capability_code"]),
                    capability_name=str(row["capability_name"]),
                    category=row.get("category"),
                    public_claim=row.get("public_claim"),
                    claim_level=str(row.get("claim_level") or "public_safe"),
                    confidence_score=float(row.get("confidence_score") or 0),
                    is_active=bool(row.get("is_active")),
                    source_count=int(row.get("source_count") or 0),
                    application_tags=_decode_tags(row.get("application_tags_json")),
                    updated_at=row.get("updated_at"),
                )
                for row in rows
            ]

            return CapabilityListPayload(
                items=items,
                total=total,
                limit=limit,
                offset=offset,
                active_total=active_total,
                inactive_total=inactive_total,
                groups_total=groups_total,
                warning=warning,
            )
        except Exception as exc:
            return CapabilityListPayload(
                items=[],
                total=0,
                limit=limit,
                offset=offset,
                active_total=0,
                inactive_total=0,
                groups_total=0,
                warning=warning or f"capabilities_unavailable: {exc}",
            )

    def get_capability_detail(self, spec_id: int) -> CapabilityDetailPayload:
        warning = self._ensure_seed()

        try:
            row = database.fetch_one(
                """
                SELECT
                  s.id,
                  s.group_code,
                  s.group_name,
                  s.capability_code,
                  s.capability_name,
                  s.category,
                  s.metric_type,
                  s.unit,
                  s.comparator,
                  s.conservative_value_num,
                  s.conservative_value_text,
                  s.advanced_value_num,
                  s.advanced_value_text,
                  s.public_claim,
                  s.internal_note,
                  s.conditions_text,
                  s.application_tags_json,
                  s.claim_level,
                  s.confidence_score,
                  s.is_active,
                  s.updated_at,
                  COUNT(DISTINCT ss.source_id) AS source_count
                FROM geo_capability_specs s
                JOIN geo_capability_profiles p ON p.id = s.profile_id
                LEFT JOIN geo_capability_spec_sources ss ON ss.spec_id = s.id
                WHERE p.profile_code = %s AND s.id = %s
                GROUP BY s.id
                """,
                params=(CAPABILITY_PROFILE_CODE, spec_id),
            )

            if not row:
                return CapabilityDetailPayload(
                    capability=None,
                    warning=warning or "capability_not_found",
                )

            search_terms = [str(row.get("capability_name") or "").strip()]
            if row.get("group_name"):
                search_terms.append(str(row["group_name"]).strip())

            article_rows: list[dict[str, Any]] = []
            for term in search_terms:
                if not term:
                    continue
                like = f"%{term}%"
                article_rows = database.fetch_all(
                    """
                    SELECT
                      id,
                      title,
                      slug,
                      publish_status,
                      quality_score,
                      updated_at
                    FROM geo_articles
                    WHERE title LIKE %s
                       OR slug LIKE %s
                       OR content_markdown LIKE %s
                       OR dim_subject LIKE %s
                    ORDER BY updated_at DESC
                    LIMIT 5
                    """,
                    params=(like, like, like, like),
                )
                if article_rows:
                    break

            recent_articles = [
                CapabilityArticleReference(
                    id=int(item["id"]),
                    title=str(item["title"]),
                    slug=str(item["slug"]),
                    publish_status=int(item.get("publish_status") or 0),
                    quality_score=int(item.get("quality_score") or 0),
                    updated_at=item.get("updated_at"),
                )
                for item in article_rows
            ]

            capability = CapabilityDetailItem(
                id=int(row["id"]),
                group_code=str(row["group_code"]),
                group_name=str(row["group_name"]),
                capability_code=str(row["capability_code"]),
                capability_name=str(row["capability_name"]),
                category=row.get("category"),
                metric_type=str(row.get("metric_type") or "range"),
                unit=row.get("unit"),
                comparator=row.get("comparator"),
                conservative_value_num=float(row["conservative_value_num"]) if row.get("conservative_value_num") is not None else None,
                conservative_value_text=row.get("conservative_value_text"),
                advanced_value_num=float(row["advanced_value_num"]) if row.get("advanced_value_num") is not None else None,
                advanced_value_text=row.get("advanced_value_text"),
                public_claim=row.get("public_claim"),
                internal_note=row.get("internal_note"),
                conditions_text=row.get("conditions_text"),
                application_tags=_decode_tags(row.get("application_tags_json")),
                claim_level=str(row.get("claim_level") or "public_safe"),
                confidence_score=float(row.get("confidence_score") or 0),
                is_active=bool(row.get("is_active")),
                source_count=int(row.get("source_count") or 0),
                updated_at=row.get("updated_at"),
                recent_articles=recent_articles,
            )

            return CapabilityDetailPayload(capability=capability, warning=warning)
        except Exception as exc:
            return CapabilityDetailPayload(
                capability=None,
                warning=warning or f"capability_detail_unavailable: {exc}",
            )

    def list_capability_sources(self, spec_id: int) -> CapabilitySourcesPayload:
        warning = self._ensure_seed()

        try:
            rows = database.fetch_all(
                """
                SELECT
                  src.id,
                  src.source_code,
                  src.source_vendor,
                  src.source_title,
                  src.source_type,
                  src.source_url,
                  src.publish_org,
                  DATE_FORMAT(src.observed_on, '%Y-%m-%d') AS observed_on,
                  src.reliability_score,
                  ss.citation_note,
                  ss.priority_weight
                FROM geo_capability_specs s
                JOIN geo_capability_profiles p ON p.id = s.profile_id
                LEFT JOIN geo_capability_spec_sources ss ON ss.spec_id = s.id
                LEFT JOIN geo_capability_sources src ON src.id = ss.source_id
                WHERE p.profile_code = %s AND s.id = %s
                ORDER BY ss.priority_weight ASC, src.id ASC
                """,
                params=(CAPABILITY_PROFILE_CODE, spec_id),
            )

            items = [
                CapabilitySourceItem(
                    id=int(row["id"]),
                    source_code=str(row["source_code"]),
                    source_vendor=str(row["source_vendor"]),
                    source_title=str(row["source_title"]),
                    source_type=str(row["source_type"]),
                    source_url=str(row["source_url"]),
                    publish_org=row.get("publish_org"),
                    observed_on=row.get("observed_on"),
                    reliability_score=float(row.get("reliability_score") or 0),
                    citation_note=row.get("citation_note"),
                    priority_weight=int(row.get("priority_weight") or 0),
                )
                for row in rows
                if row.get("id") is not None
            ]

            return CapabilitySourcesPayload(spec_id=spec_id, items=items, warning=warning)
        except Exception as exc:
            return CapabilitySourcesPayload(
                spec_id=spec_id,
                items=[],
                warning=warning or f"capability_sources_unavailable: {exc}",
            )

    def disable_capability(self, spec_id: int) -> dict[str, Any]:
        warning = self._ensure_seed()

        try:
            row = database.fetch_one(
                """
                SELECT
                  s.id,
                  s.capability_name,
                  s.is_active
                FROM geo_capability_specs s
                JOIN geo_capability_profiles p ON p.id = s.profile_id
                WHERE p.profile_code = %s AND s.id = %s
                """,
                params=(CAPABILITY_PROFILE_CODE, spec_id),
            )
            if not row:
                return {
                    "success": False,
                    "message": "能力项不存在。",
                    "error_code": "capability_not_found",
                    "warning": warning,
                }

            if not bool(row.get("is_active")):
                return {
                    "success": True,
                    "changed": False,
                    "spec_id": spec_id,
                    "capability_name": row.get("capability_name"),
                    "message": "能力项已处于停用状态。",
                    "warning": warning,
                }

            with database.connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        UPDATE geo_capability_specs s
                        JOIN geo_capability_profiles p ON p.id = s.profile_id
                        SET s.is_active = 0, s.updated_at = NOW()
                        WHERE p.profile_code = %s AND s.id = %s
                        """,
                        (CAPABILITY_PROFILE_CODE, spec_id),
                    )
                    conn.commit()
                finally:
                    cursor.close()

            return {
                "success": True,
                "changed": True,
                "spec_id": spec_id,
                "capability_name": row.get("capability_name"),
                "message": "能力项已停用。",
                "warning": warning,
            }
        except Exception as exc:
            return {
                "success": False,
                "message": f"停用能力项失败: {exc}",
                "error_code": "capability_disable_failed",
                "warning": warning,
            }


capabilities_service = CapabilitiesService()
