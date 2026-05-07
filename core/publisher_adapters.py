"""Unified publication adapters for platform-specific publishers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from core.wechat_publisher import WeChatPublisher
from core.zhihu_publisher import ZhihuPublisher

log = logging.getLogger("GEO.Adapters")


@dataclass(frozen=True)
class PublishRequest:
    platform: str
    title: str
    content_md: str
    go_live: bool = False


class PublisherAdapter(Protocol):
    platform_key: str

    def publish(self, request: PublishRequest) -> dict[str, object]: ...


class ZhihuAdapter:
    platform_key = "zhihu"

    def publish(self, request: PublishRequest) -> dict[str, object]:
        pub = ZhihuPublisher()
        if not pub.ready:
            return {"success": False, "message": "Cookie not ready"}
        if request.go_live:
            return pub.publish_and_go_live(request.title, request.content_md)
        return pub.publish(request.title, request.content_md)


class WeChatAdapter:
    platform_key = "wechat"

    def publish(self, request: PublishRequest) -> dict[str, object]:
        pub = WeChatPublisher()
        if not pub.ready:
            return {"success": False, "message": "AppID/AppSecret not configured"}
        if request.go_live:
            return pub.publish_and_go_live(request.title, request.content_md)
        return pub.publish(request.title, request.content_md)


class DryRunAdapter:
    """Simulated publisher — validates request but does not post externally."""
    platform_key = "dryrun"

    def publish(self, request: PublishRequest) -> dict[str, object]:
        return {
            "success": True,
            "status": "dry_run",
            "message": f"[DRY RUN] {request.title[:40]}...",
            "url": f"https://dryrun.local/{request.platform}/mock",
        }


ADAPTERS: dict[str, PublisherAdapter] = {
    "zhihu": ZhihuAdapter(),
    "wechat": WeChatAdapter(),
    "dryrun": DryRunAdapter(),
}


def get_publisher_adapter(platform: str) -> PublisherAdapter | None:
    return ADAPTERS.get(platform)


def list_supported_platforms() -> set[str]:
    return set(ADAPTERS.keys())


def register_adapter(platform: str, adapter: PublisherAdapter) -> None:
    ADAPTERS[platform] = adapter
    log.info("Registered adapter: %s", platform)
