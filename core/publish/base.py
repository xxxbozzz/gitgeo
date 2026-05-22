"""
Publish Layer — 统一发布编排器

所有平台通过 PlatformAdapter 接口接入。加新平台 = 写一个 Adapter 类，4 个方法。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("GEO.Publish")


@dataclass
class ArticleDTO:
    """发布文章数据对象 — 平台无关"""
    title: str
    content_html: str
    content_md: str = ""
    tags: list[str] = field(default_factory=list)
    cover_url: str = ""


@dataclass
class PublishResult:
    """发布结果 — 平台无关"""
    success: bool
    platform: str
    status: str  # draft_saved / published / failed
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    message: str = ""
    error_message: Optional[str] = None
    response_payload: Optional[dict] = None


class PlatformAdapter(ABC):
    """每个平台实现这个接口。

    4 个方法，加新平台只需写这个。
    """

    platform_key: str = ""

    @abstractmethod
    async def login(self, engine, *, headless: bool = False) -> bool:
        """首次登录。headless=False 让人工扫码。返回是否成功。"""

    @abstractmethod
    async def check_auth(self, engine) -> bool:
        """检查是否仍在登录状态。"""

    @abstractmethod
    async def publish(self, engine, article: ArticleDTO) -> PublishResult:
        """发布文章。"""

    @abstractmethod
    async def get_status(self, engine, article_id: str) -> dict:
        """查询发布后状态。"""


class PublishLayer:
    """统一发布入口。

    用法:
        layer = PublishLayer()
        layer.register(ZhihuAdapter())
        result = await layer.publish("zhihu", article)
    """

    def __init__(self):
        self._adapters: dict[str, PlatformAdapter] = {}
        self._engine = None

    def register(self, adapter: PlatformAdapter) -> None:
        self._adapters[adapter.platform_key] = adapter
        log.info("Registered adapter: %s", adapter.platform_key)

    def unregister(self, platform: str) -> None:
        self._adapters.pop(platform, None)

    async def _get_engine(self):
        if self._engine is None:
            from core.publish.engine import get_engine
            self._engine = await get_engine()
        return self._engine

    async def publish(self, platform: str, article: ArticleDTO) -> PublishResult:
        engine = await self._get_engine()
        adapter = self._adapters.get(platform)

        if adapter is None:
            return PublishResult(
                success=False, platform=platform, status="failed",
                message=f"Unsupported platform: {platform}",
                error_message="unsupported_platform",
            )

        # Check auth before publishing
        if not await adapter.check_auth(engine):
            log.warning("[%s] Auth expired, attempting re-login...", platform)
            if not await adapter.login(engine, headless=False):
                return PublishResult(
                    success=False, platform=platform, status="failed",
                    message=f"[{platform}] Auth required. Please log in manually.",
                    error_message="auth_required",
                )

        try:
            from core.publish.retry import with_retry
            return await with_retry(adapter.publish, engine, article)
        except Exception as exc:
            log.error("[%s] Publish failed after retries: %s", platform, exc)
            return PublishResult(
                success=False, platform=platform, status="failed",
                message=str(exc), error_message=str(exc),
            )

    async def publish_to_all(self, platforms: list[str], article: ArticleDTO) -> list[PublishResult]:
        results = []
        for platform in platforms:
            result = await self.publish(platform, article)
            results.append(result)
        return results

    async def login_platform(self, platform: str) -> bool:
        engine = await self._get_engine()
        adapter = self._adapters.get(platform)
        if adapter is None:
            log.error("Unknown platform: %s", platform)
            return False
        return await adapter.login(engine, headless=False)

    @property
    def supported_platforms(self) -> list[str]:
        return sorted(self._adapters.keys())


# 全局单例
publish_layer = PublishLayer()
