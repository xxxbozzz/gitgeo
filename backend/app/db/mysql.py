"""Minimal MySQL access layer for the backend API."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from mysql.connector import pooling

from backend.app.core.settings import get_settings


class MySQLDatabase:
    """Lightweight connection-pool wrapper."""

    def __init__(self) -> None:
        self._pool: pooling.MySQLConnectionPool | None = None

    def _pool_config(self) -> dict[str, Any]:
        settings = get_settings()
        return {
            "pool_name": settings.db_pool_name,
            "pool_size": settings.db_pool_size,
            "user": settings.db_user,
            "password": settings.db_password,
            "host": settings.db_host,
            "port": settings.db_port,
            "database": settings.db_name,
            "raise_on_warnings": False,
            "autocommit": True,
        }

    def _ensure_pool(self) -> pooling.MySQLConnectionPool:
        if self._pool is None:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(**self._pool_config())
        return self._pool

    @contextmanager
    def connection(self) -> Iterator[mysql.connector.MySQLConnection]:
        conn = self._ensure_pool().get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def ping(self) -> bool:
        try:
            with self.connection() as conn:
                conn.ping(reconnect=True, attempts=1, delay=0)
            return True
        except Exception:
            return False

    def fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        with self.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, params or ())
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                cursor.close()

    def fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                cursor.close()

    def fetch_value(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        field: str = "value",
        default: Any = None,
    ) -> Any:
        row = self.fetch_one(sql, params=params)
        if not row:
            return default
        return row.get(field, default)


database = MySQLDatabase()
