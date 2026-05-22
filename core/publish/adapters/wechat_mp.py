"""
WeChat MP Adapter — CloakBrowser 模拟登录微信公众号后台 + 发布草稿。

流程：
  1. 打开 mp.weixin.qq.com
  2. 若无登录态 → 扫码（headless=False）
  3. 登录态保存到 config/auth/wechat_mp.json
  4. 后续发布：加载登录态 → 新建草稿 → 保存
"""

from __future__ import annotations

import asyncio
import logging

from core.publish.base import ArticleDTO, PlatformAdapter, PublishResult

log = logging.getLogger("GEO.WeChatMP")

MP_URL = "https://mp.weixin.qq.com"


class WeChatMPAdapter(PlatformAdapter):
    platform_key = "wechat_mp"

    async def login(self, engine, *, headless: bool = False) -> bool:
        context = await engine.new_context(mobile=False)
        page = await context.new_page()

        try:
            await page.goto(f"{MP_URL}/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1",
                            wait_until="domcontentloaded")
            log.info("WeChat MP login page opened. Scan QR code within 120s...")

            for _ in range(120):
                await asyncio.sleep(1)
                url = page.url
                if "appmsg_edit" in url:
                    log.info("WeChat MP login detected.")
                    await engine.save_auth("wechat_mp", context)
                    return True

            log.error("WeChat MP login timeout.")
            return False
        except Exception as exc:
            log.error("WeChat MP login error: %s", exc)
            return False
        finally:
            await context.close()

    async def check_auth(self, engine) -> bool:
        context = await engine.get_context("wechat_mp")
        page = await context.new_page()
        try:
            await page.goto(f"{MP_URL}/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1",
                            wait_until="domcontentloaded", timeout=15000)
            if "appmsg_edit" in page.url:
                return True
            log.warning("WeChat MP auth expired.")
            return False
        except Exception as exc:
            log.warning("WeChat MP auth check failed: %s", exc)
            return False
        finally:
            await context.close()

    async def publish(self, engine, article: ArticleDTO) -> PublishResult:
        context = await engine.get_context("wechat_mp")
        page = await context.new_page()

        try:
            # 打开新建图文页面
            await page.goto(
                f"{MP_URL}/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1",
                wait_until="domcontentloaded", timeout=20000,
            )
            await asyncio.sleep(3)

            # 输入标题
            title_input = page.locator('#title, [placeholder*="标题"], input.title-input').first
            await title_input.fill(article.title[:64])
            await asyncio.sleep(1)

            # 输入正文（微信编辑器是 iframe 内的 contenteditable div）
            content_frame = page.frame_locator('#ueditor_0').first if await page.locator('#ueditor_0').count() > 0 else None
            if content_frame:
                content_area = content_frame.locator('[contenteditable="true"]').first
            else:
                content_area = page.locator('#editor, [contenteditable="true"]').first

            await content_area.click()
            await page.keyboard.type(article.content_html, delay=10)
            await asyncio.sleep(3)

            # 点击保存按钮
            save_btn = page.locator('#js_save, button:has-text("保存"), a:has-text("保存")').first
            if await save_btn.is_visible():
                await save_btn.click()
                await asyncio.sleep(3)

            return PublishResult(
                success=True,
                platform="wechat_mp",
                status="draft_saved",
                message="Draft saved to WeChat MP drafts.",
            )

        except Exception as exc:
            log.error("WeChat MP publish error: %s", exc)
            return PublishResult(
                success=False, platform="wechat_mp", status="failed",
                message=str(exc), error_message=str(exc),
            )
        finally:
            await context.close()

    async def get_status(self, engine, article_id: str) -> dict:
        return {"article_id": article_id, "status": "unknown"}
