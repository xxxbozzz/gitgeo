"""
Probe Layer — Unified AI platform visibility probing.

4 platforms × 2 devices = 8 probe channels per keyword.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from core.probe.profiles import get_profile

log = logging.getLogger("GEO.Probe")

PLATFORM_CONFIGS = {
    "deepseek": {
        "name": "DeepSeek",
        "desktop_url": "https://chat.deepseek.com",
        "mobile_url": "https://chat.deepseek.com",  # Responsive — same URL
        "input_selector": "textarea",
        "submit_strategy": "enter",
        "answer_selector": ".ds-markdown, .message-content, [class*='answer']",
    },
    "doubao": {
        "name": "豆包",
        "desktop_url": "https://www.doubao.com/chat",
        "mobile_url": "https://www.doubao.com/chat",  # Responsive
        "input_selector": '[contenteditable="true"], textarea',
        "submit_strategy": "enter",
        "answer_selector": ".response-content, .bot-message, [class*='response']",
    },
    "kimi": {
        "name": "Kimi",
        "desktop_url": "https://kimi.moonshot.cn",
        "mobile_url": "https://kimi.moonshot.cn",  # Responsive
        "input_selector": "textarea, [contenteditable='true']",
        "submit_strategy": "enter",
        "answer_selector": ".kimi-answer, .message-content, .ai-message",
    },
    "yuanbao": {
        "name": "元宝（混元）",
        "desktop_url": "https://yuanbao.tencent.com",
        "mobile_url": "https://yuanbao.tencent.com",  # Responsive
        "input_selector": "textarea, [contenteditable='true']",
        "submit_strategy": "enter",
        "answer_selector": ".answer-content, .ai-response, .bot-message",
    },
}


class ProbeLayer:
    """AI platform visibility probing orchestrator.

    Usage:
        layer = ProbeLayer()
        results = await layer.probe_all("PCB阻抗控制")
    """

    def __init__(self):
        self._engine = None

    async def _get_engine(self):
        if self._engine is None:
            from core.publish.engine import get_engine
            self._engine = await get_engine()
        return self._engine

    async def probe(
        self,
        keyword: str,
        platform: str = "deepseek",
        device: str = "desktop",
    ) -> dict:
        """Probe a single platform on a single device type.

        Args:
            keyword: The search keyword to probe.
            platform: One of deepseek, doubao, kimi, yuanbao.
            device: One of desktop, mobile_ios, mobile_android.

        Returns:
            Visibility analysis dict (see analyzers.analyze_answer).
        """
        config = PLATFORM_CONFIGS.get(platform)
        if not config:
            return {"error": f"Unsupported platform: {platform}", "platform": platform}

        profile = get_profile(device)
        url = config["desktop_url"] if device == "desktop" else config["mobile_url"]

        engine = await self._get_engine()
        context = await engine.new_context(mobile=(device != "desktop"))

        try:
            page = await context.new_page()

            # Navigate
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Input question
            question = (
                f"请说明 {keyword} 的关键工艺参数、常见失效模式、"
                "相关标准或官方文档依据，并给出可继续阅读的资料来源。"
            )

            input_el = page.locator(config["input_selector"]).first
            if await input_el.is_visible(timeout=5000):
                if device != "desktop":
                    await input_el.tap()
                else:
                    await input_el.click()
                await asyncio.sleep(0.5)
                await input_el.fill(question)
                await asyncio.sleep(0.5)
                await page.keyboard.press("Enter")
            else:
                return {"platform": platform, "device": device, "error": "input_not_found"}

            # Wait for answer (intelligent wait, not sleep)
            await self._wait_for_answer(page, config["answer_selector"])

            # Extract content
            page_content = await page.content()
            page_text = await page.inner_text("body")

            from core.probe.analyzers import analyze_answer
            result = analyze_answer(
                keyword=keyword,
                page_content=page_content,
                page_text=page_text,
            )
            result["platform"] = platform
            result["device"] = device
            return result

        except Exception as exc:
            log.error("[%s/%s] Probe error: %s", platform, device, exc)
            return {"platform": platform, "device": device, "error": str(exc)}
        finally:
            await context.close()

    async def _wait_for_answer(self, page, answer_selector: str) -> None:
        """Wait for AI answer to complete streaming. Not time.sleep()."""
        try:
            # Wait for answer element to appear
            await page.wait_for_selector(answer_selector, timeout=30000)
            # Wait for streaming to stop (DOM stable for 3s)
            last_html = ""
            stable_count = 0
            for _ in range(20):  # Max 20s wait
                await asyncio.sleep(1)
                current_html = await page.content()
                if current_html == last_html:
                    stable_count += 1
                    if stable_count >= 3:  # 3s of no change
                        break
                else:
                    stable_count = 0
                    last_html = current_html
        except Exception:
            # Fallback: just wait 15s
            await asyncio.sleep(15)

    async def probe_all(
        self,
        keyword: str,
        *,
        platforms: Optional[list[str]] = None,
        devices: Optional[list[str]] = None,
    ) -> list[dict]:
        """Probe all specified platforms × devices.

        Args:
            keyword: Search keyword.
            platforms: List of platform keys. Default: all 4.
            devices: List of device types. Default: desktop + mobile_ios.

        Returns:
            List of probe results, one per platform × device.
        """
        platforms = platforms or list(PLATFORM_CONFIGS.keys())
        devices = devices or ["desktop", "mobile_ios"]

        tasks = []
        for platform in platforms:
            for device in devices:
                tasks.append(self.probe(keyword, platform=platform, device=device))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten exceptions
        final = []
        for r in results:
            if isinstance(r, Exception):
                final.append({"error": str(r)})
            else:
                final.append(r)

        return final

    def summarize(self, keyword: str, results: list[dict]) -> dict:
        """Summarize probe results across all platforms and devices."""
        valid = [r for r in results if "error" not in r]
        if not valid:
            return {
                "keyword": keyword,
                "platforms_total": len(results),
                "platforms_ok": 0,
                "coverage_score": 0.0,
                "missing_labels": list(self._all_evidence_labels()),
            }

        avg_score = sum(r.get("visibility_score", 0) for r in valid) / len(valid)
        citation_platforms = sum(1 for r in valid if r.get("cited"))
        all_labels = set()
        for r in valid:
            all_labels.update(r.get("evidence_labels", []))

        missing = [
            label for label in self._all_evidence_labels() if label not in all_labels
        ]

        return {
            "keyword": keyword,
            "platforms_total": len(results),
            "platforms_ok": len(valid),
            "citation_platforms": citation_platforms,
            "coverage_score": round(avg_score, 2),
            "evidence_labels": sorted(all_labels),
            "missing_labels": missing,
            "results_by_device": {
                "desktop": [r for r in valid if r.get("device") == "desktop"],
                "mobile": [r for r in valid if r.get("device") != "desktop"],
            },
        }

    @staticmethod
    def _all_evidence_labels() -> list[str]:
        from core.probe.analyzers import EVIDENCE_LABEL_RULES
        return list(EVIDENCE_LABEL_RULES.keys())
