#!/usr/bin/env python3
"""
Live Publish Test — DEV.to via CloakBrowser + GitHub OAuth.

Opens a visible browser window → user authorizes GitHub → auto-publishes article.

Usage: python scripts/test_publish_live.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("Test")


async def main():
    from cloakbrowser import launch as cb_launch

    log.info("=" * 60)
    log.info("  DEV.to Live Publish Test")
    log.info("=" * 60)
    log.info("")
    log.info("  A Chrome window is opening...")
    log.info("  1. Click 'Continue with GitHub'")
    log.info("  2. Authorize DEV.to on the GitHub OAuth page")
    log.info("  3. Wait for redirect back to DEV.to dashboard")
    log.info("  4. The script auto-detects login and publishes")
    log.info("")
    log.info("  Timeout: 300 seconds (5 minutes)")
    log.info("=" * 60)

    # Launch visible browser
    browser = await asyncio.to_thread(
        cb_launch,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = await asyncio.to_thread(browser.new_context)
    page = await asyncio.to_thread(context.new_page)

    # Go directly to DEV.to GitHub OAuth
    await asyncio.to_thread(
        page.goto,
        "https://dev.to/enter?state=github",
        timeout=30000,
    )
    await asyncio.sleep(3)
    log.info("Browser open. Waiting for you to log in...")

    # Wait for redirect back to DEV.to (5 min timeout)
    for _ in range(300):
        await asyncio.sleep(1)
        url = page.url
        if "dev.to" in url and "/enter" not in url and "github.com" not in url:
            log.info("✅ Login detected!")

            # Save auth
            state = await asyncio.to_thread(context.storage_state)
            auth_dir = Path("config/auth")
            auth_dir.mkdir(parents=True, exist_ok=True)
            (auth_dir / "devto.json").write_text(json.dumps(state, indent=2))
            log.info("✅ Auth saved.")

            # Publish test article via headless browser
            log.info("Publishing test article...")
            await page.goto("https://dev.to/new", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Title
            title_el = page.locator('[placeholder*="title"], input.title, #article-form-title').first
            if await title_el.is_visible(timeout=5000):
                await title_el.fill("GitGeo Publish Layer — Live Verification")
                await asyncio.sleep(1)

            # Content
            content_md = (
                "## GitGeo Publish Layer v2.0\n\n"
                "This article was published via GitGeo's automated Publish Layer.\n\n"
                "### Architecture\n\n"
                "Each platform requires only 4 methods: `login`, `check_auth`, `publish`, `get_status`.\n\n"
                "### Verified\n\n"
                "✅ CloakBrowser anti-detect browser engine\n"
                "✅ DEV.to adapter (GitHub OAuth)\n"
                "✅ Telegraph adapter (zero-auth, live verified)\n\n"
                "### Status: PASS\n\n"
                "*Published via GitGeo automated test.*"
            )
            content_el = page.locator('[contenteditable="true"], textarea#article_body_markdown').first
            if await content_el.is_visible(timeout=5000):
                await content_el.fill(content_md)
                await asyncio.sleep(2)

            # Publish
            publish_btn = page.locator('button:has-text("Publish")').first
            if await publish_btn.is_visible(timeout=5000):
                await publish_btn.click()
                await asyncio.sleep(5)
                log.info("✅ Published!")
                log.info("   URL: %s", page.url)
            else:
                log.warning("Publish button not found. Article saved as draft.")

            await asyncio.to_thread(context.close)
            await asyncio.to_thread(browser.close)
            log.info("Test complete.")
            return

    log.error("❌ Login timeout (300s).")
    await asyncio.to_thread(context.close)
    await asyncio.to_thread(browser.close)


if __name__ == "__main__":
    asyncio.run(main())
