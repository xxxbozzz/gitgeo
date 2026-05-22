"""
Zhihu Adapter — CloakBrowser 模拟真人登录 + 发布。

流程：
  1. 打开 zhuanlan.zhihu.com/write
  2. 若未登录 → 扫码（headless=False）
  3. 登录态保存到 config/auth/zhihu.json
  4. 后续发布：加载登录态 → 写文章 → 发布
"""

from __future__ import annotations

import asyncio
import logging
import os

from core.publish.base import ArticleDTO, PlatformAdapter, PublishResult

log = logging.getLogger("GEO.Zhihu")

AUTH_FILE = "config/auth/zhihu.json"
ZHIHU_WRITE_URL = "https://zhuanlan.zhihu.com/write"


class ZhihuAdapter(PlatformAdapter):
    platform_key = "zhihu"

    async def login(self, engine, *, headless: bool = False) -> bool:
        context = await engine.new_context(mobile=False)
        page = await context.new_page()

        try:
            await page.goto("https://www.zhihu.com/signin", wait_until="domcontentloaded")
            log.info("Zhihu login page opened. Scan QR code within 120s...")

            # 等待登录成功（URL 跳到首页或 /write 可访问）
            for _ in range(120):
                await asyncio.sleep(1)
                url = page.url
                if "/signin" not in url:
                    log.info("Zhihu login detected.")
                    await engine.save_auth("zhihu", context)
                    return True

            log.error("Zhihu login timeout.")
            return False
        except Exception as exc:
            log.error("Zhihu login error: %s", exc)
            return False
        finally:
            await context.close()

    async def check_auth(self, engine) -> bool:
        context = await engine.get_context("zhihu")
        page = await context.new_page()
        try:
            resp = await page.goto(ZHIHU_WRITE_URL, wait_until="domcontentloaded", timeout=15000)
            url = page.url
            # 如果跳到登录页或首页，说明登录过期
            if "/signin" in url or "login" in url.lower():
                log.warning("Zhihu auth expired (redirected to login).")
                return False
            if resp and resp.status < 400:
                return True
            return False
        except Exception as exc:
            log.warning("Zhihu auth check failed: %s", exc)
            return False
        finally:
            await context.close()

    async def publish(self, engine, article: ArticleDTO) -> PublishResult:
        context = await engine.get_context("zhihu")
        page = await context.new_page()

        try:
            await page.goto(ZHIHU_WRITE_URL, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)

            # 输入标题
            title_input = page.locator('[placeholder*="输入文章标题"], .title-input, [data-testid="title"]').first
            await title_input.click()
            await _human_type(page, article.title)
            await asyncio.sleep(1)

            # 输入正文（知乎使用富文本编辑器）
            content_area = page.locator('.public-DraftEditor-content, [contenteditable="true"], .editor-content').first
            await content_area.click()
            await _human_type(page, article.content_html)
            await asyncio.sleep(2)

            # 点击发布按钮
            publish_btn = page.locator('button:has-text("发布"), button:has-text("发布文章"), [data-testid="publish"]').first
            if await publish_btn.is_visible():
                await publish_btn.click()
                await asyncio.sleep(3)

            # 获取文章 URL
            article_url = page.url
            article_id = article_url.rstrip("/").split("/")[-1] if "/p/" in article_url else None

            return PublishResult(
                success=True,
                platform="zhihu",
                status="published",
                external_id=article_id,
                external_url=article_url,
                message=f"Published: {article_url}",
            )

        except Exception as exc:
            log.error("Zhihu publish error: %s", exc)
            return PublishResult(
                success=False, platform="zhihu", status="failed",
                message=str(exc), error_message=str(exc),
            )
        finally:
            await context.close()

    async def get_status(self, engine, article_id: str) -> dict:
        context = await engine.get_context("zhihu")
        page = await context.new_page()
        try:
            url = f"https://zhuanlan.zhihu.com/p/{article_id}"
            resp = await page.goto(url, wait_until="domcontentloaded")
            return {"article_id": article_id, "url": url, "status": resp.status}
        finally:
            await context.close()


async def _human_type(page, text: str):
    """模拟人类打字 — 随机间隔，偶尔打错纠正。"""
    import random
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.03, 0.12))
        if random.random() < 0.03 and len(text) > 5:
            await page.keyboard.type("x")
            await asyncio.sleep(random.uniform(0.08, 0.25))
            await page.keyboard.press("Backspace")
