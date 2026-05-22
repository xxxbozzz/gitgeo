"""
数据库管理器 (Database Manager) — PostgreSQL
=============================================
本模块提供 PostgreSQL 数据库的连接池管理和 CRUD 操作。
负责与 geo_articles / geo_keywords / geo_links 三张核心表交互。

API 保持向后兼容，所有调用方无需改动。

使用方法：
    from core.db_manager import db_manager
    db_manager.save_article({...})
"""

import os
import json
import hashlib
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool, extras


class DatabaseManager:
    """知识引擎数据库管理器 — 基于 PostgreSQL 连接池"""

    def __init__(self):
        try:
            db_port = int(os.environ.get("DB_PORT", "5432"))
        except ValueError:
            db_port = 5432

        self.db_config = {
            "user": os.environ.get("DB_USER", "geo_app"),
            "password": os.environ.get("DB_PASSWORD", "change-this-password"),
            "host": os.environ.get("DB_HOST", "localhost"),
            "dbname": os.environ.get("DB_NAME", "geo_engine"),
            "port": db_port,
        }
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                **self.db_config,
            )
            print("✅ PostgreSQL 连接池初始化成功")
        except Exception as e:
            print(f"❌ 数据库连接池初始化失败: {e}")
            self._pool = None

    def get_connection(self):
        """从连接池获取一个连接"""
        if not self._pool:
            return None
        try:
            return self._pool.getconn()
        except Exception as e:
            print(f"❌ 获取数据库连接失败: {e}")
            return None

    def _return_connection(self, cnx):
        """归还连接到池"""
        if cnx and self._pool:
            try:
                self._pool.putconn(cnx)
            except Exception:
                pass

    @contextmanager
    def _cursor(self, cnx, *, dictionary=False):
        """Context manager for cursor lifecycle."""
        factory = extras.RealDictCursor if dictionary else None
        cursor = cnx.cursor(cursor_factory=factory)
        try:
            yield cursor
        finally:
            cursor.close()

    # ──────────────────── 文章操作 ────────────────────

    @staticmethod
    def _calculate_hash(content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def article_exists(self, slug: str) -> bool:
        cnx = self.get_connection()
        if not cnx:
            return False
        try:
            with self._cursor(cnx) as cursor:
                cursor.execute("SELECT id FROM geo_articles WHERE slug = %s", (slug,))
                return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            self._return_connection(cnx)

    def is_duplicate_content(self, content_hash: str) -> bool:
        cnx = self.get_connection()
        if not cnx:
            return False
        try:
            with self._cursor(cnx) as cursor:
                cursor.execute("SELECT id FROM geo_articles WHERE content_hash = %s", (content_hash,))
                return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            self._return_connection(cnx)

    def save_article_with_result(self, article_data: dict, status: int = 0) -> dict:
        """
        保存文章到数据库，并返回入库结果。
        参数:
            article_data: 包含 title, slug, content, meta, dim_* 的字典
            status: 发布状态 (0=草稿, 1=待审, 2=已发, 3=归档)
        返回:
            {"success": bool, "article_id": int|None, "action": str, "reason": str|None}
        """
        cnx = self.get_connection()
        if not cnx:
            return {"success": False, "article_id": None, "action": "none", "reason": "db_unavailable"}

        try:
            with self._cursor(cnx) as cursor:
                content_hash = self._calculate_hash(article_data.get("content", ""))

                if self.is_duplicate_content(content_hash):
                    print(f"⚠️  检测到重复内容: {article_data.get('title')}，已跳过。")
                    return {"success": False, "article_id": None, "action": "skipped", "reason": "duplicate_content"}

                meta_json_str = json.dumps(article_data.get("meta", {}), ensure_ascii=False)
                cursor.execute(
                    """
                    INSERT INTO geo_articles AS a
                        (title, slug, meta_json, content_markdown, content_hash,
                         publish_status, dim_subject, dim_action, dim_attribute)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (slug) DO UPDATE SET
                        title = EXCLUDED.title,
                        meta_json = EXCLUDED.meta_json,
                        content_markdown = EXCLUDED.content_markdown,
                        content_hash = EXCLUDED.content_hash,
                        updated_at = NOW()
                    RETURNING a.id, (xmax = 0) AS is_insert
                    """,
                    (
                        article_data.get("title"),
                        article_data.get("slug"),
                        meta_json_str,
                        article_data.get("content"),
                        content_hash,
                        status,
                        article_data.get("dim_subject"),
                        article_data.get("dim_action"),
                        article_data.get("dim_attribute"),
                    ),
                )
                row = cursor.fetchone()
                article_id = row["id"] if row else None
                is_insert = row.get("is_insert", True) if row else True
                action = "created" if is_insert else "updated"
                cnx.commit()
                print(f"✅ 文章已保存: {article_data.get('title')} (ID: {article_id}, 状态: {status})")
                return {"success": True, "article_id": article_id, "action": action, "reason": None}

        except Exception as e:
            print(f"❌ 保存文章失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return {"success": False, "article_id": None, "action": "none", "reason": str(e)}
        finally:
            self._return_connection(cnx)

    def save_article(self, article_data: dict, status: int = 0) -> bool:
        result = self.save_article_with_result(article_data, status=status)
        return bool(result.get("success"))

    # ──────────────────── 关键词操作 ────────────────────

    def add_keyword(self, keyword: str, search_volume: int = 0, difficulty: int = 0) -> bool:
        cnx = self.get_connection()
        if not cnx:
            return False
        try:
            with self._cursor(cnx) as cursor:
                cursor.execute(
                    """
                    INSERT INTO geo_keywords (keyword, search_volume, difficulty)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (keyword) DO NOTHING
                    """,
                    (keyword, search_volume, difficulty),
                )
                cnx.commit()
            return True
        except Exception as e:
            print(f"❌ 添加关键词失败: {e}")
            return False
        finally:
            self._return_connection(cnx)

    def merge_article_meta(self, article_id: int, patch: dict) -> bool:
        cnx = self.get_connection()
        if not cnx:
            return False
        try:
            with self._cursor(cnx, dictionary=True) as cursor:
                cursor.execute(
                    "SELECT meta_json FROM geo_articles WHERE id = %s LIMIT 1",
                    (article_id,),
                )
                row = cursor.fetchone() or {}
                current_meta = row.get("meta_json")
                if isinstance(current_meta, str) and current_meta:
                    try:
                        current_meta = json.loads(current_meta)
                    except Exception:
                        current_meta = {}
                if not isinstance(current_meta, dict):
                    current_meta = {}
                current_meta.update(patch or {})
                cursor.execute(
                    "UPDATE geo_articles SET meta_json = %s, updated_at = NOW() WHERE id = %s",
                    (json.dumps(current_meta, ensure_ascii=False), article_id),
                )
                cnx.commit()
            return True
        except Exception as e:
            print(f"❌ 合并文章元数据失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return False
        finally:
            self._return_connection(cnx)


# 全局单例
db_manager = DatabaseManager()
