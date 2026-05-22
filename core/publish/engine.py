"""
Browser Engine — CloakBrowser 反检测浏览器

CloakBrowser 是 Playwright 的 drop-in 替换，57 个 C++ patches 消除 WebDriver 指纹。
API 与 Playwright 完全兼容。

安装: pip install cloakbrowser
无 CloakBrowser 时自动降级为 Playwright。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("GEO.Engine")

AUTH_DIR = Path(os.environ.get("GEO_AUTH_DIR", "config/auth"))
AUTH_DIR.mkdir(parents=True, exist_ok=True)

_engine_instance = None


def _get_browser_launcher():
    """Try CloakBrowser first, fall back to Playwright."""
    try:
        from cloakbrowser import launch
        log.info("Using CloakBrowser (anti-detect)")
        return launch, "cloakbrowser"
    except ImportError:
        from playwright.async_api import async_playwright
        log.warning("CloakBrowser not installed. Falling back to Playwright (no anti-detect).")
        log.warning("Install: pip install cloakbrowser")

        async def _pw_launch(**kwargs):
            pw = await async_playwright().start()
            return await pw.chromium.launch(**kwargs)
        return _pw_launch, "playwright"


class BrowserEngine:
    """反检测浏览器引擎 — 管理 browser 实例和 contexts。

    用法:
        engine = await BrowserEngine.create()
        context = await engine.get_context("zhihu")   # 自动加载保存的登录状态
        page = await context.new_page()
        # ... 操作 ...
        await engine.save_auth("zhihu", context)       # 保存登录状态
    """

    def __init__(self):
        self._browser = None
        self._launcher = None
        self._backend = "playwright"

    async def start(self) -> None:
        if self._browser is not None:
            return
        launch_fn, self._backend = _get_browser_launcher()
        self._launcher = launch_fn
        self._browser = await launch_fn(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        log.info("Browser engine started (backend: %s)", self._backend)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            log.info("Browser engine stopped")

    @property
    def backend(self) -> str:
        return self._backend

    async def get_context(self, platform: str, *, mobile: bool = False):
        """获取一个 browser context，自动加载保存的登录状态。"""
        await self.start()
        auth_file = AUTH_DIR / f"{platform}.json"

        if auth_file.exists():
            import json
            state = json.loads(auth_file.read_text())
            context = await self._browser.new_context(storage_state=state)
            log.debug("Loaded auth state for %s", platform)
        else:
            context = await self._browser.new_context()

        if mobile:
            context = await self._apply_mobile_profile(context)

        return context

    async def save_auth(self, platform: str, context) -> None:
        """保存登录状态到文件。"""
        state = await context.storage_state()
        AUTH_DIR.mkdir(parents=True, exist_ok=True)
        auth_file = AUTH_DIR / f"{platform}.json"
        import json
        auth_file.write_text(json.dumps(state, indent=2))
        log.info("Auth state saved for %s", platform)

    async def new_context(self, *, mobile: bool = False):
        """创建一个全新的 context（不用已保存的状态）。"""
        await self.start()
        context = await self._browser.new_context()
        if mobile:
            context = await self._apply_mobile_profile(context)
        return context

    async def _apply_mobile_profile(self, context):
        """给 context 注入移动端配置。"""
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)
        return context


async def get_engine() -> BrowserEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = BrowserEngine()
        await _engine_instance.start()
    return _engine_instance
