"""
Dry-Run Publisher
=================
模拟发布流程，不实际发送到外部平台。用于测试和验证。
每个适配器都输出完整的请求摘要、模拟响应和验证结果。

用法:
    from core.dryrun_publisher import DryRunPublisher
    dr = DryRunPublisher()
    result = dr.publish("zhihu", title="test", content_md="# test")
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from core.publisher_adapters import (
    get_publisher_adapter,
    list_supported_platforms,
)

log = logging.getLogger("GEO.DryRun")


class DryRunPublisher:
    """模拟发布器 — 不实际发到外部平台，但输出完整请求摘要和模拟响应"""

    def __init__(self):
        self._results: list[dict[str, Any]] = []

    def publish(
        self,
        platform: str,
        title: str,
        content_md: str,
        go_live: bool = False,
    ) -> dict[str, Any]:
        """模拟发布一篇文章到指定平台"""
        adapter = get_publisher_adapter(platform)
        adapter_available = adapter is not None

        request_summary = {
            "platform": platform,
            "title": title[:100],
            "content_length": len(content_md),
            "content_preview": content_md[:200],
            "go_live": go_live,
            "timestamp": time.time(),
        }

        response = {
            "platform": platform,
            "status": "dry_run",
            "adapter_available": adapter_available,
        }

        if adapter_available:
            response.update({
                "success": True,
                "message": f"[DRY RUN] Would publish to {platform}: {title[:40]}...",
                "url": f"https://dryrun.local/{platform}/article/mock-{int(time.time())}",
                "request_summary": request_summary,
                "adapter_type": adapter.platform_key,
            })
        else:
            response.update({
                "success": False,
                "message": f"[DRY RUN] No adapter for platform: {platform}",
                "request_summary": request_summary,
            })

        self._results.append(response)
        log.info("Dry run [%s]: %s", platform, "available" if adapter_available else "missing")
        return response

    def batch_publish(
        self,
        platforms: list[str],
        title: str,
        content_md: str,
        go_live: bool = False,
    ) -> list[dict[str, Any]]:
        """批量模拟发布到多个平台"""
        return [self.publish(p, title, content_md, go_live) for p in platforms]

    def verify_all_adapters(self) -> dict[str, Any]:
        """验证所有已注册适配器是否可用（不实际发布）"""
        results = {}
        for platform_key in list_supported_platforms():
            adapter = get_publisher_adapter(platform_key)
            results[platform_key] = {
                "available": adapter is not None,
                "adapter_type": type(adapter).__name__ if adapter else None,
            }
        return results

    def get_results(self) -> list[dict[str, Any]]:
        """获取历史模拟结果"""
        return self._results
