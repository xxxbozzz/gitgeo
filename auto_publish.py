#!/usr/bin/env python3
"""
自动发文调度器 (Auto Publisher) — PostgreSQL + SQLAlchemy 2.0 async
====================================================================
从数据库读取已通过质检但未发布的文章，自动发布到知乎和微信公众号。

用法:
    DB_HOST=localhost python auto_publish.py           # 发布到草稿箱
    DB_HOST=localhost python auto_publish.py --live     # 直接发布（谨慎）

环境变量（.env 文件）:
    GEO_LLM_API_KEY / DEEPSEEK_API_KEY — LLM API 密钥
    DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME — PostgreSQL 连接
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from backend.app.db.session import _get_session_factory
from backend.app.repositories.publication import PublicationRepository
from backend.app.repositories.article import ArticleRepository
from core.publisher_adapters import get_publisher_adapter, list_supported_platforms, PublishRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("Publisher")


async def get_unpublished_articles(limit: int = 5) -> list[dict]:
    """获取已通过质检但未外发的文章"""
    factory = _get_session_factory()
    async with factory() as session:
        repo = ArticleRepository(session)
        articles, _ = await repo.list_articles(
            status="approved", min_score=80, limit=limit,
        )
        return [
            {"id": a.id, "title": a.title, "content_markdown": a.content_markdown}
            for a in articles
        ]


async def publish_article_to_platform(
    article_id: int, title: str, content_md: str,
    platform: str, go_live: bool,
) -> dict:
    adapter = get_publisher_adapter(platform)
    if adapter is None:
        return {"platform": platform, "status": "error", "message": f"Unsupported platform: {platform}"}

    try:
        result = adapter.publish(PublishRequest(
            platform=platform, title=title, content_md=content_md, go_live=go_live,
        ))
        return {
            "platform": platform,
            "status": result.get("status", "unknown"),
            "message": str(result.get("message", "")),
            "url": result.get("url"),
        }
    except Exception as exc:
        return {"platform": platform, "status": "error", "message": str(exc)}


async def async_main(go_live: bool = False, limit: int = 3, platform: str = "all"):
    log.info("=" * 50)
    log.info("  自动发文调度器启动 (PostgreSQL/async)")
    log.info(f"  模式: {'直接发布' if go_live else '保存草稿'}")
    log.info(f"  平台: {platform}")
    log.info("=" * 50)

    articles = await get_unpublished_articles(limit)
    if not articles:
        log.info("没有待发布的文章（publish_status=1 且 score≥80）")
        return

    platforms = (
        ["zhihu", "wechat", "dryrun"]
        if platform == "all"
        else [platform]
    )

    for i, article in enumerate(articles, 1):
        title = str(article.get("title", ""))
        content_md = str(article.get("content_markdown", ""))
        log.info(f"\n[{i}/{len(articles)}] {title[:40]}...")

        for plat in platforms:
            result = await publish_article_to_platform(
                int(article["id"]), title, content_md, plat, go_live,
            )
            log.info(
                "  %s [%s]: %s",
                result.get("platform"),
                result.get("status"),
                result.get("message"),
            )

        await asyncio.sleep(5)

    log.info("\n✅ 发布完成")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="直接发布（不仅保存草稿）")
    parser.add_argument("--limit", type=int, default=3, help="每次最多发布篇数")
    parser.add_argument("--platform", choices=["all", "zhihu", "wechat", "dryrun"], default="all")
    args = parser.parse_args()

    asyncio.run(async_main(
        go_live=args.live,
        limit=args.limit,
        platform=args.platform,
    ))


if __name__ == "__main__":
    main()
