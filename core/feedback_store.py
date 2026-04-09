"""
GEO 反馈仓库 (Feedback Store)
============================
负责持久化：
1. AI 平台探测结果
2. 关键词级 Prompt 反馈摘要
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.db_manager import db_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = PROJECT_ROOT / "database" / "feedback_schema.sql"


def _json_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


class FeedbackStore:
    """监测结果与 Prompt 反馈持久化仓库。"""

    def __init__(self) -> None:
        self._schema_ready = False

    def ensure_schema(self) -> bool:
        if self._schema_ready:
            return True
        if not SCHEMA_FILE.exists():
            print(f"❌ 反馈表结构文件不存在: {SCHEMA_FILE}")
            return False

        cnx = db_manager.get_connection()
        if not cnx:
            return False

        cursor = cnx.cursor()
        try:
            statement_lines: list[str] = []
            for raw_line in SCHEMA_FILE.read_text(encoding="utf-8").splitlines():
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("--"):
                    continue
                statement_lines.append(raw_line)
                if stripped.endswith(";"):
                    statement = "\n".join(statement_lines).strip()
                    if statement:
                        cursor.execute(statement)
                    statement_lines = []
            cnx.commit()
            self._schema_ready = True
            return True
        except Exception as exc:
            print(f"❌ 创建反馈表失败: {exc}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return False
        finally:
            cursor.close()
            cnx.close()

    def save_probe_result(
        self,
        *,
        keyword: str,
        platform: str,
        result: dict[str, Any],
        keyword_id: int | None = None,
        article_id: int | None = None,
    ) -> None:
        if not self.ensure_schema():
            return

        cnx = db_manager.get_connection()
        if not cnx:
            return
        cursor = cnx.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO geo_probe_results (
                    keyword_id, keyword, article_id, platform,
                    mentioned, cited, visibility_rank, visibility_score,
                    evidence_labels_json, source_hits_json, snapshot_text, detail_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    keyword_id,
                    keyword,
                    article_id,
                    platform,
                    1 if result.get("mentioned") else 0,
                    1 if result.get("cited") else 0,
                    result.get("rank"),
                    result.get("visibility_score"),
                    _json_or_none(result.get("evidence_labels")),
                    _json_or_none(result.get("source_hits")),
                    result.get("snapshot"),
                    _json_or_none(result),
                ),
            )
            cnx.commit()
        except Exception as exc:
            print(f"❌ 保存探测结果失败: {exc}")
            try:
                cnx.rollback()
            except Exception:
                pass
        finally:
            cursor.close()
            cnx.close()

    def upsert_keyword_feedback(
        self,
        *,
        keyword: str,
        keyword_id: int | None = None,
        article_id: int | None = None,
        citation_score: float | None = None,
        probe_coverage_score: float | None = None,
        feedback_labels: list[str] | None = None,
        article_signals: dict[str, Any] | None = None,
        probe_summary: dict[str, Any] | None = None,
        suggested_keywords: list[str] | None = None,
        prompt_guidance: str | None = None,
    ) -> None:
        if not self.ensure_schema():
            return

        cnx = db_manager.get_connection()
        if not cnx:
            return
        cursor = cnx.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO geo_keyword_feedback (
                    keyword_id, keyword, article_id, citation_score, probe_coverage_score,
                    feedback_labels_json, article_signals_json, probe_summary_json,
                    suggested_keywords_json, prompt_guidance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    keyword_id = VALUES(keyword_id),
                    article_id = VALUES(article_id),
                    citation_score = VALUES(citation_score),
                    probe_coverage_score = VALUES(probe_coverage_score),
                    feedback_labels_json = VALUES(feedback_labels_json),
                    article_signals_json = VALUES(article_signals_json),
                    probe_summary_json = VALUES(probe_summary_json),
                    suggested_keywords_json = VALUES(suggested_keywords_json),
                    prompt_guidance = VALUES(prompt_guidance)
                """,
                (
                    keyword_id,
                    keyword,
                    article_id,
                    citation_score,
                    probe_coverage_score,
                    _json_or_none(feedback_labels),
                    _json_or_none(article_signals),
                    _json_or_none(probe_summary),
                    _json_or_none(suggested_keywords),
                    prompt_guidance,
                ),
            )
            cnx.commit()
        except Exception as exc:
            print(f"❌ 保存关键词反馈失败: {exc}")
            try:
                cnx.rollback()
            except Exception:
                pass
        finally:
            cursor.close()
            cnx.close()

    def get_prompt_context(self, keyword: str, limit: int = 3) -> list[dict[str, Any]]:
        if not self.ensure_schema():
            return []

        cnx = db_manager.get_connection()
        if not cnx:
            return []
        cursor = cnx.cursor(dictionary=True)
        try:
            like_value = f"%{keyword.strip()}%"
            cursor.execute(
                """
                SELECT keyword, citation_score, probe_coverage_score, feedback_labels_json,
                       article_signals_json, probe_summary_json, suggested_keywords_json,
                       prompt_guidance, updated_at
                FROM geo_keyword_feedback
                WHERE keyword = %s OR keyword LIKE %s
                ORDER BY (keyword = %s) DESC, updated_at DESC
                LIMIT %s
                """,
                (keyword, like_value, keyword, limit),
            )
            rows = cursor.fetchall()
            for row in rows:
                for field in (
                    "feedback_labels_json",
                    "article_signals_json",
                    "probe_summary_json",
                    "suggested_keywords_json",
                ):
                    raw_value = row.get(field)
                    if raw_value:
                        try:
                            row[field] = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
                        except Exception:
                            pass
            return rows
        except Exception as exc:
            print(f"❌ 读取 Prompt 反馈失败: {exc}")
            return []
        finally:
            cursor.close()
            cnx.close()


feedback_store = FeedbackStore()
