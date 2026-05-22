"""
Unified publication adapters — delegates to Publish Layer.

Backward-compatible interface for auto_publish.py and publications_service.py.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from core.publish.base import ArticleDTO, publish_layer
from core.publish.adapters.zhihu import ZhihuAdapter
from core.publish.adapters.wechat_mp import WeChatMPAdapter
from core.publish.adapters.dryrun import DryRunAdapter

log = logging.getLogger("GEO.Adapters")

# Register adapters on import
publish_layer.register(ZhihuAdapter())
publish_layer.register(WeChatMPAdapter())
publish_layer.register(DryRunAdapter())


@dataclass(frozen=True)
class PublishRequest:
    platform: str
    title: str
    content_md: str
    go_live: bool = False


class PublisherAdapter:
    """Adapter wrapper for backward compatibility.

    Usage (old API):
        adapter = get_publisher_adapter("zhihu")
        result = adapter.publish(PublishRequest(...))
    """

    def __init__(self, platform_key: str):
        self.platform_key = platform_key

    def publish(self, request: PublishRequest) -> dict:
        article = ArticleDTO(
            title=request.title,
            content_html=request.content_md,  # Will be converted to HTML by adapter
            content_md=request.content_md,
        )
        try:
            result = asyncio.run(publish_layer.publish(self.platform_key, article))
            return {
                "success": result.success,
                "status": result.status,
                "external_id": result.external_id,
                "external_url": result.external_url,
                "url": result.external_url,  # Backward compat
                "message": result.message,
                "error_message": result.error_message,
            }
        except Exception as exc:
            return {
                "success": False,
                "status": "failed",
                "message": str(exc),
                "error_message": str(exc),
            }


# Backward-compatible adapter map
ADAPTERS: dict[str, PublisherAdapter] = {
    key: PublisherAdapter(key)
    for key in publish_layer.supported_platforms
}


def get_publisher_adapter(platform: str) -> PublisherAdapter | None:
    return ADAPTERS.get(platform)


def list_supported_platforms() -> set[str]:
    return set(ADAPTERS.keys())


def register_adapter(platform: str, adapter: PublisherAdapter) -> None:
    ADAPTERS[platform] = adapter
    log.info("Registered adapter: %s", platform)
