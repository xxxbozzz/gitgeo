#!/usr/bin/env python3
"""
自动发文调度器 (Auto Publisher)
==============================
从数据库读取已通过质检但未发布的文章，自动发布到知乎和微信公众号。

用法:
    DB_HOST=localhost python auto_publish.py           # 发布到草稿箱
    DB_HOST=localhost python auto_publish.py --live     # 直接发布（谨慎）
"""

import argparse
import logging
import os
import time

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("MYSQL_CONNECTOR_PYTHON_TELEMETRY", "0")

from dotenv import load_dotenv
load_dotenv()

from backend.app.db.mysql import database
from backend.app.services.publications_service import publications_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("Publisher")


def get_unpublished_articles(limit: int = 5) -> list:
    """获取已通过质检但未外发的文章"""
    return database.fetch_all(
        """
        SELECT id, title
        FROM geo_articles
        WHERE publish_status = 1 AND quality_score >= 80
        ORDER BY created_at ASC
        LIMIT %s
        """,
        params=(limit,),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="直接发布（不仅保存草稿）")
    parser.add_argument("--limit", type=int, default=3, help="每次最多发布篇数")
    parser.add_argument("--platform", choices=["all", "zhihu", "wechat"], default="all")
    args = parser.parse_args()

    log.info("=" * 50)
    log.info("  自动发文调度器启动")
    log.info(f"  模式: {'直接发布' if args.live else '保存草稿'}")
    log.info(f"  平台: {args.platform}")
    log.info("=" * 50)

    articles = get_unpublished_articles(args.limit)
    if not articles:
        log.info("没有待发布的文章（publish_status=1 且 score≥80）")
        return

    log.info(f"待发布: {len(articles)} 篇")

    platforms = ["zhihu", "wechat"] if args.platform == "all" else [args.platform]

    for i, article in enumerate(articles, 1):
        title = article["title"]
        log.info(f"\n[{i}/{len(articles)}] {title[:40]}...")
        publish_result = publications_service.publish_article(
            int(article["id"]),
            platforms=platforms,
            go_live=args.live,
            trigger_mode="auto",
        )

        for platform_result in publish_result.get("results", []):
            log.info(
                "  %s [%s]: %s",
                platform_result.get("platform"),
                platform_result.get("status"),
                platform_result.get("message"),
            )

        if publish_result.get("success"):
            log.info("  ✅ 已记录平台发布审计")
        else:
            log.warning("  ⚠️ 未达到目标发布状态: %s", publish_result.get("message"))

        time.sleep(5)  # 间隔 5 秒

    log.info("\n✅ 发布完成")


if __name__ == "__main__":
    main()
