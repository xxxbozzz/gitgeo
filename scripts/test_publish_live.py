#!/usr/bin/env python3
"""
Live Publish Test — DEV.to via CloakBrowser + GitHub OAuth.

Step 1: Opens visible browser → user clicks GitHub OAuth → auth saved
Step 2: Publishes a test article via headless browser using saved auth

Usage:
  python scripts/test_publish_live.py
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


async def login_once() -> bool:
    """Open visible browser, let user log in via GitHub OAuth, save auth state."""
    from cloakbrowser import launch as cb_launch

    log.info("=" * 60)
    log.info("  STEP 1: Login (visible browser)")
    log.info("  Click 'Sign in with GitHub' → Authorize DEV.to")
    log.info("  You have 120 seconds before timeout.")
    log.info("=" * 60)

    # Launch visible browser
    browser = await asyncio.to_thread(
        cb_launch,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = await asyncio.to_thread(browser.new_context)
    page = await asyncio.to_thread(context.new_page)

    await asyncio.to_thread(page.goto, "https://dev.to/enter", timeout=30000)
    await asyncio.sleep(2)
    log.info("Browser opened. Waiting for login...")

    # Wait for redirect back to DEV.to
    for _ in range(120):
        await asyncio.sleep(1)
        url = page.url
        if "dev.to" in url and "/enter" not in url and "github.com" not in url:
            log.info("✅ Login detected.")

            # Save auth state
            state = await asyncio.to_thread(context.storage_state)
            auth_dir = Path("config/auth")
            auth_dir.mkdir(parents=True, exist_ok=True)
            (auth_dir / "devto.json").write_text(json.dumps(state, indent=2))
            log.info("✅ Auth saved to config/auth/devto.json")

            await asyncio.to_thread(context.close)
            await asyncio.to_thread(browser.close)
            return True

    log.error("❌ Login timeout (120s).")
    await asyncio.to_thread(context.close)
    await asyncio.to_thread(browser.close)
    return False


async def publish_test() -> dict:
    """Publish a test article using saved auth via headless CloakBrowser."""
    from core.publish.base import publish_layer, ArticleDTO

    log.info("=" * 60)
    log.info("  STEP 2: Publish test article (headless)")
    log.info("=" * 60)

    article = ArticleDTO(
        title="GitGeo Automated Publish Test",
        content_md="""## Hello from GitGeo

This is a test article published automatically by **GitGeo's Publish Layer**.

### What is GitGeo?

GitGeo is an open-source GEO (Generative Engine Optimization) content engine.
It automates discovery → generation → quality scoring → AI visibility probing → publishing.

### How was this published?

1. **CloakBrowser** — anti-detect browser (Playwright + 57 C++ patches)
2. **DevToAdapter** — `PlatformAdapter` interface (4 methods)
3. **PublishLayer** — orchestrator with auth, retry, error recovery

### Adding a new platform = 1 class

```python
class MyPlatformAdapter(PlatformAdapter):
    platform_key = "myplatform"
    async def login(self, engine, *, headless=False): ...
    async def check_auth(self, engine): ...
    async def publish(self, engine, article): ...
    async def get_status(self, engine, article_id): ...
```

### Status

Published via GitGeo Publish Layer v2.0 at **{timestamp}**.

---
*🤖 Automated test — will self-delete*
""",
        tags=["testing", "automation", "gitgeo", "geo"],
    )

    result = await publish_layer.publish("devto", article)

    if result.success:
        log.info("✅ Publish SUCCESS!")
        log.info("   URL: %s", result.external_url)
    else:
        log.error("❌ Publish FAILED.")
        log.error("   %s: %s", result.error_message, result.message)

    return {"success": result.success, "url": result.external_url, "message": result.message}


async def main():
    log.info("GitGeo Live Publish Test — DEV.to")
    log.info("")

    # Step 1: Login (visible browser, user clicks GitHub OAuth)
    if not await login_once():
        log.error("Aborting: login failed.")
        return

    # Step 2: Publish (headless, uses saved auth)
    result = await publish_test()

    log.info("")
    log.info("=" * 60)
    if result["success"]:
        log.info("  ✅ ALL TESTS PASSED")
        log.info("  Article: %s", result["url"])
    else:
        log.info("  ❌ PUBLISH FAILED: %s", result["message"])
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
