"""
GEO 运行记录仓库 (Job Store)
===========================
为 GEO 主流程提供工程化任务追踪：
1. 自动创建 run / step 表
2. 记录每个关键词的整体运行状态
3. 记录生成、质检、返修、导出、内链、关键词绑定等步骤结果
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.db_manager import db_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = PROJECT_ROOT / "database" / "job_runtime_schema.sql"


def _json_or_none(data: dict[str, Any] | None) -> str | None:
    if not data:
        return None
    return json.dumps(data, ensure_ascii=False)


class JobStore:
    """轻量运行记录仓库"""

    def __init__(self):
        self._schema_ready = False

    def ensure_schema(self) -> bool:
        """创建运行记录相关表"""
        if self._schema_ready:
            return True
        if not SCHEMA_FILE.exists():
            print(f"❌ 运行记录表结构文件不存在: {SCHEMA_FILE}")
            return False

        cnx = db_manager.get_connection()
        if not cnx:
            return False

        try:
            cnx.raise_on_warnings = False
        except Exception:
            pass

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
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            message = str(e)
                            if "already exists" in message or "1050" in message:
                                statement_lines = []
                                continue
                            raise
                    statement_lines = []
            cnx.commit()
            self._schema_ready = True
            return True
        except Exception as e:
            print(f"❌ 创建运行记录表失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return False
        finally:
            cursor.close()
            cnx.close()

    def start_run(
        self,
        run_uid: str,
        keyword_id: int | None,
        keyword: str,
        trigger_mode: str,
        run_type: str = "article_generation",
        detail: dict[str, Any] | None = None,
    ) -> int | None:
        """创建一条 run 记录"""
        if not self.ensure_schema():
            return None

        cnx = db_manager.get_connection()
        if not cnx:
            return None
        cursor = cnx.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO geo_job_runs
                (run_uid, run_type, trigger_mode, keyword_id, keyword, status, detail_json)
                VALUES (%s, %s, %s, %s, %s, 'running', %s)
                """,
                (run_uid, run_type, trigger_mode, keyword_id, keyword, _json_or_none(detail)),
            )
            cnx.commit()
            return int(cursor.lastrowid)
        except Exception as e:
            print(f"❌ 创建运行记录失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return None
        finally:
            cursor.close()
            cnx.close()

    def update_run(
        self,
        job_run_id: int | None,
        *,
        current_step: str | None = None,
        article_id: int | None = None,
        status: str | None = None,
        retry_count: int | None = None,
        error_message: str | None = None,
        detail: dict[str, Any] | None = None,
        finished: bool = False,
    ) -> None:
        """更新 run 状态"""
        if not job_run_id:
            return
        cnx = db_manager.get_connection()
        if not cnx:
            return

        cursor = cnx.cursor()
        try:
            fields = []
            values: list[Any] = []
            if current_step is not None:
                fields.append("current_step = %s")
                values.append(current_step)
            if article_id is not None:
                fields.append("article_id = %s")
                values.append(article_id)
            if status is not None:
                fields.append("status = %s")
                values.append(status)
            if retry_count is not None:
                fields.append("retry_count = %s")
                values.append(retry_count)
            if error_message is not None:
                fields.append("error_message = %s")
                values.append(error_message)
            if detail is not None:
                fields.append("detail_json = %s")
                values.append(_json_or_none(detail))
            if finished:
                fields.append("finished_at = NOW()")

            if not fields:
                return

            cursor.execute(
                f"UPDATE geo_job_runs SET {', '.join(fields)} WHERE id = %s",
                (*values, job_run_id),
            )
            cnx.commit()
        except Exception as e:
            print(f"❌ 更新运行记录失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
        finally:
            cursor.close()
            cnx.close()

    def start_step(
        self,
        job_run_id: int | None,
        step_code: str,
        step_name: str,
        *,
        attempt_no: int = 1,
        article_id: int | None = None,
        detail: dict[str, Any] | None = None,
    ) -> int | None:
        """创建一条 step 记录"""
        if not job_run_id:
            return None

        self.update_run(job_run_id, current_step=step_code, article_id=article_id)

        cnx = db_manager.get_connection()
        if not cnx:
            return None
        cursor = cnx.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO geo_job_steps
                (job_run_id, step_code, step_name, attempt_no, status, article_id, detail_json)
                VALUES (%s, %s, %s, %s, 'running', %s, %s)
                """,
                (job_run_id, step_code, step_name, attempt_no, article_id, _json_or_none(detail)),
            )
            cnx.commit()
            return int(cursor.lastrowid)
        except Exception as e:
            print(f"❌ 创建步骤记录失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return None
        finally:
            cursor.close()
            cnx.close()

    def finish_step(
        self,
        step_id: int | None,
        *,
        status: str,
        article_id: int | None = None,
        error_message: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """结束某个 step"""
        if not step_id:
            return
        cnx = db_manager.get_connection()
        if not cnx:
            return
        cursor = cnx.cursor()
        try:
            fields = [
                "status = %s",
                "finished_at = NOW()",
            ]
            values: list[Any] = [status]
            if article_id is not None:
                fields.append("article_id = %s")
                values.append(article_id)
            if error_message is not None:
                fields.append("error_message = %s")
                values.append(error_message)
            if detail is not None:
                fields.append("detail_json = %s")
                values.append(_json_or_none(detail))
            cursor.execute(
                f"UPDATE geo_job_steps SET {', '.join(fields)} WHERE id = %s",
                (*values, step_id),
            )
            cnx.commit()
        except Exception as e:
            print(f"❌ 更新步骤记录失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
        finally:
            cursor.close()
            cnx.close()


job_store = JobStore()
