"""
AI Search Engine Prober — delegates to Probe Layer.

4 platforms × 2 devices = 8 probe channels per keyword.
Backward-compatible with old ActiveProber API.
"""

from __future__ import annotations

import asyncio
import logging

from core.probe.base import ProbeLayer
from core.target_profile import TARGET_ENTITY_ALIASES, TARGET_ENTITY_NAME

log = logging.getLogger("GEO.Prober")

_probe_layer = ProbeLayer()


class ActiveProber:
    """AI visibility probe — delegates to ProbeLayer.

    Backward-compatible API:
        prober = ActiveProber()
        result = prober.probe("keyword", platform="deepseek")
        results = prober.probe_all("keyword")
        summary = prober.summarize_results("keyword", results)
    """

    PLATFORMS = {
        "deepseek": {"name": "DeepSeek"},
        "doubao": {"name": "豆包"},
        "kimi": {"name": "Kimi"},
        "hunyuan": {"name": "元宝（混元）"},  # alias for yuanbao
        "yuanbao": {"name": "元宝（混元）"},
    }

    def probe(self, keyword: str, platform: str = "deepseek") -> dict:
        """Probe a single platform. Sync wrapper for backward compat."""
        # Map old platform names
        platform_key = platform
        if platform == "hunyuan":
            platform_key = "yuanbao"

        try:
            return asyncio.run(
                _probe_layer.probe(keyword, platform=platform_key, device="desktop")
            )
        except Exception as exc:
            return {
                "platform": platform,
                "keyword": keyword,
                "error": str(exc),
            }

    def probe_all(
        self,
        keyword: str,
        platforms: list[str] | None = None,
    ) -> list[dict]:
        """Probe all specified platforms on desktop + mobile."""
        target_platforms = platforms or ["deepseek", "kimi", "doubao", "yuanbao"]
        try:
            return asyncio.run(
                _probe_layer.probe_all(
                    keyword,
                    platforms=target_platforms,
                    devices=["desktop", "mobile_ios"],
                )
            )
        except Exception as exc:
            return [{"error": str(exc)}]

    def summarize_results(self, keyword: str, results: list[dict]) -> dict:
        """Summarize probe results. Backward-compatible."""
        return _probe_layer.summarize(keyword, results)
