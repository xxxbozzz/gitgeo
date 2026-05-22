"""
DryRun Adapter — 本地测试用，不真发。
"""

from __future__ import annotations

import logging

from core.publish.base import ArticleDTO, PlatformAdapter, PublishResult

log = logging.getLogger("GEO.DryRun")


class DryRunAdapter(PlatformAdapter):
    platform_key = "dryrun"

    async def login(self, engine, *, headless: bool = False) -> bool:
        log.info("[DryRun] Login (no-op).")
        return True

    async def check_auth(self, engine) -> bool:
        return True

    async def publish(self, engine, article: ArticleDTO) -> PublishResult:
        log.info("[DryRun] Publishing: %s", article.title[:40])
        return PublishResult(
            success=True,
            platform="dryrun",
            status="published",
            external_id="dryrun-001",
            external_url="https://dryrun.local/mock",
            message="[DRY RUN] Published successfully (no external platform).",
        )

    async def get_status(self, engine, article_id: str) -> dict:
        return {"article_id": article_id, "status": "published"}
