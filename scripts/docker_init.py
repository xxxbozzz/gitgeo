"""
Docker build-time initialization — pre-download browser binaries.

Runs during `docker build`, not at container runtime.
Saves ~140MB download on first container start.
"""

import sys


def init_cloakbrowser():
    """Pre-download CloakBrowser anti-detect Chromium (~140MB)."""
    try:
        from cloakbrowser import launch
        b = launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        b.close()
        print("CloakBrowser Chromium pre-downloaded successfully.")
    except Exception as e:
        print(f"WARNING: CloakBrowser pre-download failed: {e}")
        print("It will download on first launch() at container runtime.")
        # Non-fatal — CloakBrowser auto-downloads if not pre-cached


def verify_playwright():
    """Verify Playwright browsers are functional."""
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        for browser_type in [p.chromium, p.firefox, p.webkit]:
            b = browser_type.launch()
            b.close()
            print(f"Playwright {browser_type.name}: OK")
        p.stop()
    except Exception as e:
        print(f"WARNING: Playwright verification failed: {e}")


def verify_postgres():
    """Verify asyncpg can import (connection not required at build time)."""
    try:
        import asyncpg
        print(f"asyncpg {asyncpg.__version__}: OK")
    except ImportError:
        print("WARNING: asyncpg not available")


if __name__ == "__main__":
    print("GitGeo Docker Init — pre-downloading browser binaries...")
    verify_postgres()
    init_cloakbrowser()
    verify_playwright()
    print("Docker init complete.")
