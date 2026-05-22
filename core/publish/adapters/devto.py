"""
DEV.to Adapter — GitHub OAuth login → CloakBrowser publish.

DEV.to is a developer blogging platform with:
  - GitHub OAuth login (no phone verification)
  - Markdown editor
  - Immediate public URL after publishing
  - Free, no approval needed

Test flow:
  1. Open dev.to/enter → click "Sign in with GitHub"
  2. GitHub OAuth → authorize DEV.to
  3. Click "Write a Post" → fill title + content
  4. Click "Publish" → get article URL
"""

from __future__ import annotations

import asyncio
import logging

from core.publish.base import ArticleDTO, PlatformAdapter, PublishResult

log = logging.getLogger("GEO.DEVto")

DEVTO_URL = "https://dev.to"


class DevToAdapter(PlatformAdapter):
    platform_key = "devto"

    async def login(self, engine, *, headless: bool = False) -> bool:
        """GitHub OAuth login — user needs a GitHub account."""
        context = await engine.new_context(mobile=False)
        page = await context.new_page()

        try:
            # Step 1: Go to DEV.to enter page
            await page.goto(f"{DEVTO_URL}/enter", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Step 2: Click "Sign in with GitHub"
            github_btn = page.locator(
                'a[href*="github"], button:has-text("GitHub"), '
                '.github-auth, [data-testid="github-signin"]'
            ).first

            if await github_btn.is_visible(timeout=5000):
                await github_btn.click()
            else:
                log.error("GitHub sign-in button not found on DEV.to /enter")
                return False

            # Step 3: Wait for GitHub OAuth page
            await asyncio.sleep(3)

            # If already authorized on GitHub, we skip to callback
            # If not, user needs to approve in the visible browser

            # Step 4: Wait for redirect back to DEV.to
            for _ in range(60):
                await asyncio.sleep(1)
                url = page.url
                if "dev.to" in url and "/enter" not in url.split("?")[0]:
                    log.info("DEV.to login success.")
                    await engine.save_auth("devto", context)
                    return True

            log.error("DEV.to login timeout (GitHub OAuth took >60s).")
            return False
        except Exception as exc:
            log.error("DEV.to login error: %s", exc)
            return False
        finally:
            await context.close()

    async def check_auth(self, engine) -> bool:
        context = await engine.get_context("devto")
        page = await context.new_page()
        try:
            await page.goto(f"{DEVTO_URL}/new", wait_until="domcontentloaded", timeout=15000)
            url = page.url
            if "/enter" in url or "/signin" in url:
                return False
            return True
        except Exception:
            return False
        finally:
            await context.close()

    async def publish(self, engine, article: ArticleDTO) -> PublishResult:
        context = await engine.get_context("devto")
        page = await context.new_page()

        try:
            # Step 1: Go to new article page
            await page.goto(f"{DEVTO_URL}/new", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)

            # Step 2: Fill title
            title_input = page.locator(
                '[placeholder*="title"], [aria-label*="title"], '
                '#article-form-title, input.title'
            ).first

            if await title_input.is_visible(timeout=5000):
                await title_input.click()
                await asyncio.sleep(0.3)
                await title_input.fill(article.title)
            else:
                return PublishResult(
                    success=False, platform="devto", status="failed",
                    message="Title input not found on DEV.to /new",
                    error_message="input_not_found",
                )

            await asyncio.sleep(1)

            # Step 3: Fill content (DEV.to uses a contenteditable or textarea)
            content_el = page.locator(
                '[contenteditable="true"], textarea#article_body_markdown, '
                '[aria-label*="body"], #article_body_markdown'
            ).first

            if await content_el.is_visible(timeout=5000):
                await content_el.click()
                await asyncio.sleep(0.3)
                await content_el.fill(article.content_md)
            else:
                return PublishResult(
                    success=False, platform="devto", status="failed",
                    message="Content editor not found on DEV.to /new",
                    error_message="input_not_found",
                )

            await asyncio.sleep(2)

            # Step 4: Add tags
            try:
                tag_input = page.locator('[placeholder*="tag"], .tag-input input').first
                if await tag_input.is_visible(timeout=3000):
                    for tag in (article.tags or [])[:4]:
                        await tag_input.fill(tag)
                        await asyncio.sleep(0.5)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(0.5)
            except Exception:
                pass

            # Step 5: Click Publish
            publish_btn = page.locator(
                'button:has-text("Publish"), [data-testid="publish"], '
                'button.publish-button, button[aria-label*="publish"]'
            ).first

            if await publish_btn.is_visible(timeout=5000):
                await publish_btn.click()
                await asyncio.sleep(5)
            else:
                return PublishResult(
                    success=False, platform="devto", status="failed",
                    message="Publish button not found on DEV.to",
                    error_message="button_not_found",
                )

            # Step 6: Get article URL
            article_url = page.url
            slug = None
            if "/" in article_url:
                parts = article_url.rstrip("/").split("/")
                slug = parts[-1] if parts else None

            return PublishResult(
                success=True,
                platform="devto",
                status="published",
                external_id=slug,
                external_url=article_url,
                message=f"Published on DEV.to: {article_url}",
            )

        except Exception as exc:
            log.error("DEV.to publish error: %s", exc)
            return PublishResult(
                success=False, platform="devto", status="failed",
                message=str(exc), error_message=str(exc),
            )
        finally:
            await context.close()

    async def get_status(self, engine, article_id: str) -> dict:
        context = await engine.get_context("devto")
        page = await context.new_page()
        try:
            url = f"{DEVTO_URL}/{article_id}"
            resp = await page.goto(url, wait_until="domcontentloaded")
            return {"article_id": article_id, "url": url, "status": resp.status if resp else "unknown"}
        finally:
            await context.close()
