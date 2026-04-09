#!/usr/bin/env python3
"""
一键修复脚本 — 修复低分文章 + 全量内链
=======================================
直接用 LLM 修复所有 <80 分的文章，然后为所有已发布文章建立内链。
不走 CrewAI 流水线，直接调用 DeepSeek API。

用法:
    DB_HOST=localhost OTEL_SDK_DISABLED=true venv/bin/python fix_and_link.py
"""

import os, sys, time, hashlib, logging

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("MYSQL_CONNECTOR_PYTHON_TELEMETRY", "0")
os.environ.setdefault("DB_HOST", "localhost")

from dotenv import load_dotenv
load_dotenv()

import mysql.connector
from langchain_openai import ChatOpenAI
from core.quality_checker import QualityChecker
from core.auto_fixer import AutoFixer
from core.linker import AutoLinker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("FIX")

# ─── LLM ───
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.3,
    max_tokens=8000,
)

PASS_THRESHOLD = 80
MAX_ATTEMPTS = 3


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root_password"),
        database=os.getenv("DB_NAME", "geo_knowledge_engine"),
        connection_timeout=5,
    )


def update_article(article_id, **fields):
    cnx = get_db()
    cursor = cnx.cursor()
    sets = ", ".join(f"{k}=%s" for k in fields)
    cursor.execute(f"UPDATE geo_articles SET {sets} WHERE id=%s", (*fields.values(), article_id))
    cnx.commit()
    cursor.close()
    cnx.close()


def fix_article(article_id: int, title: str, content: str) -> bool:
    """修复单篇文章直到通过质检或放弃"""
    checker = QualityChecker()
    fixer = AutoFixer()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        score, report = checker.evaluate_article(title, content)
        failed = [k for k, v in report.items() if not v]
        passed_dims = [k for k, v in report.items() if v]

        log.info(f"  第{attempt}/{MAX_ATTEMPTS}次 [{score}分] ✅{','.join(passed_dims)} ❌{','.join(failed)}")
        update_article(article_id, quality_score=score)

        if score >= PASS_THRESHOLD:
            update_article(article_id, publish_status=1, quality_score=score)
            log.info(f"  ✅ 通过! [{score}分]")
            return True

        if attempt >= MAX_ATTEMPTS:
            log.warning(f"  💀 放弃 [{score}分]")
            return False

        # 生成修复指令
        fix_prompt = fixer.generate_fix_prompt(content, report)
        if not fix_prompt:
            log.warning("  AutoFixer 未生成指令")
            return False

        try:
            result = llm.invoke(fix_prompt)
            new_content = result.content if hasattr(result, "content") else str(result)

            if len(new_content.strip()) < 500:
                log.warning(f"  返修结果过短 ({len(new_content)}字符)")
                continue

            content_hash = hashlib.md5(new_content.encode("utf-8")).hexdigest()
            update_article(article_id, content_markdown=new_content, content_hash=content_hash)
            content = new_content
            log.info(f"  🔧 返修完成 ({len(new_content)}字符)")

        except Exception as e:
            log.error(f"  LLM错误: {e}")
            continue

        time.sleep(1)  # API 冷却

    return False


def main():
    log.info("=" * 60)
    log.info("  一键修复脚本启动")
    log.info("=" * 60)

    cnx = get_db()
    cursor = cnx.cursor(dictionary=True)

    # ═══ 阶段 1: 修复低分文章 ═══
    log.info("\n📋 阶段 1: 修复低于80分的文章")
    cursor.execute(
        "SELECT id, title, content_markdown, quality_score "
        "FROM geo_articles "
        "WHERE (quality_score < 80 OR quality_score IS NULL) "
        "AND content_markdown IS NOT NULL "
        "AND LENGTH(content_markdown) > 200 "
        "ORDER BY quality_score DESC"
    )
    low_articles = cursor.fetchall()
    log.info(f"  发现 {len(low_articles)} 篇需要修复")

    fixed_count = 0
    failed_count = 0
    for i, article in enumerate(low_articles, 1):
        title = article["title"] or ""
        content = article["content_markdown"] or ""
        score = article["quality_score"] or 0

        log.info(f"\n[{i}/{len(low_articles)}] #{article['id']} [{score}分] {title[:40]}...")

        if fix_article(article["id"], title, content):
            fixed_count += 1
        else:
            failed_count += 1

        time.sleep(2)  # API 冷却

    log.info(f"\n📊 修复结果: ✅通过 {fixed_count} | ❌未通过 {failed_count}")

    # ═══ 阶段 2: 全量内链 ═══
    log.info("\n🔗 阶段 2: 全量内链构建")
    linker = AutoLinker()

    cursor.execute("SELECT id, title FROM geo_articles WHERE publish_status >= 1 ORDER BY id")
    published = cursor.fetchall()
    log.info(f"  {len(published)} 篇已发布文章")

    total_out, total_in = 0, 0
    for article in published:
        r = linker.link_article(article["id"])
        total_out += r["outgoing"]
        total_in += r["incoming"]
        if r["outgoing"] or r["incoming"]:
            log.info(f"  [{article['id']}] 出{r['outgoing']} 入{r['incoming']}")

    log.info(f"\n🔗 内链结果: 出链 {total_out}, 入链 {total_in}")

    # ═══ 最终统计 ═══
    cursor.execute("SELECT COUNT(*) as c FROM geo_articles WHERE publish_status >= 1")
    total_pub = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) as c FROM geo_links")
    total_links = cursor.fetchone()["c"]
    cursor.execute("SELECT ROUND(AVG(quality_score),1) as avg FROM geo_articles WHERE quality_score > 0")
    avg = cursor.fetchone()["avg"]

    log.info("\n" + "=" * 60)
    log.info(f"  ✅ 完成! 已发布: {total_pub}篇 | 内链: {total_links}条 | 平均分: {avg}")
    log.info("=" * 60)

    cursor.close()
    cnx.close()


if __name__ == "__main__":
    main()
