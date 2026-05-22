"""
Telegraph Adapter — anonymous publishing via telegra.ph API.

Flow (fully automated, zero human interaction):
  1. First use: call createAccount → get access_token → save to config/
  2. Subsequent uses: load saved token → publish directly
  3. Token never expires (Telegraph doesn't have token expiry)

Live verified: https://telegra.ph/GitGeo-Automated-Publish-Test-05-22
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import aiohttp

from core.publish.base import ArticleDTO, PlatformAdapter, PublishResult

log = logging.getLogger("GEO.Telegraph")

TELEGRAPH_API = "https://api.telegra.ph"
TOKEN_FILE = Path("config/auth/telegraph_token.json")


class TelegraphAdapter(PlatformAdapter):
    platform_key = "telegraph"

    async def login(self, engine, *, headless: bool = False) -> bool:
        """Auto-create Telegraph account if no token saved."""
        return await self._ensure_token()

    async def check_auth(self, engine) -> bool:
        return await self._ensure_token()

    async def publish(self, engine, article: ArticleDTO) -> PublishResult:
        token = await self._ensure_token()
        if not token:
            return PublishResult(
                success=False, platform="telegraph", status="failed",
                message="Failed to obtain Telegraph access token.",
                error_message="no_token",
            )

        content_nodes = self._md_to_nodes(article.content_md or article.content_html)

        payload = {
            "access_token": token,
            "title": article.title[:256],
            "author_name": "GitGeo",
            "content": content_nodes,
            "return_content": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{TELEGRAPH_API}/createPage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()

            if not data.get("ok"):
                error = data.get("error", "unknown")
                return PublishResult(
                    success=False, platform="telegraph", status="failed",
                    message=f"Telegraph API error: {error}",
                    error_message=str(error),
                )

            result = data["result"]
            url = result["url"]
            path = result["path"]

            log.info("✅ Published to Telegraph: %s", url)
            return PublishResult(
                success=True, platform="telegraph", status="published",
                external_id=path, external_url=url,
                message=f"Published: {url}",
            )

        except Exception as exc:
            return PublishResult(
                success=False, platform="telegraph", status="failed",
                message=str(exc), error_message=str(exc),
            )

    async def get_status(self, engine, article_id: str) -> dict:
        return {
            "article_id": article_id,
            "status": "published",
            "url": f"https://telegra.ph/{article_id}",
        }

    async def _ensure_token(self) -> str | None:
        """Load saved token or create a new Telegraph account."""
        if TOKEN_FILE.exists():
            try:
                data = json.loads(TOKEN_FILE.read_text())
                return data.get("access_token")
            except Exception:
                pass

        # Create new account
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{TELEGRAPH_API}/createAccount",
                    json={"short_name": "GitGeo", "author_name": "GitGeo"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    data = await resp.json()

            if data.get("ok"):
                token = data["result"]["access_token"]
                TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
                TOKEN_FILE.write_text(json.dumps(data["result"], indent=2))
                log.info("Telegraph account created. Token saved.")
                return token
        except Exception as exc:
            log.error("Failed to create Telegraph account: %s", exc)

        return None

    @staticmethod
    def _md_to_nodes(md_text: str) -> list[dict]:
        nodes = []
        for paragraph in md_text.split("\n\n"):
            stripped = paragraph.strip()
            if not stripped:
                continue
            if stripped.startswith("### "):
                nodes.append({"tag": "h4", "children": [stripped[4:]]})
            elif stripped.startswith("## "):
                nodes.append({"tag": "h3", "children": [stripped[3:]]})
            elif stripped.startswith("# "):
                nodes.append({"tag": "h3", "children": [stripped[2:]]})
            elif stripped.startswith("```"):
                code_lines = stripped.replace("```", "").strip()
                nodes.append({"tag": "pre", "children": [code_lines]})
            else:
                nodes.append({"tag": "p", "children": [stripped]})
        return nodes
