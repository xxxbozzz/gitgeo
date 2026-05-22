#!/usr/bin/env python3
"""
gitgeo 项目初始化脚本 (PostgreSQL)
==================================
首次启动时自动执行：建表 → 导种子数据 → 打印就绪状态

幂等：已存在的表和数据不会重复创建。

用法:
    python scripts/init_project.py              # 自动初始化
    python scripts/init_project.py --reset      # 强制重建（危险）
"""

import os
import sys
import json
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [init] %(message)s")
log = logging.getLogger("init")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(PROJECT_ROOT, "database")
SEED_FILE = os.path.join(PROJECT_ROOT, "seed_topics.json")

PG_INIT_FILE = os.path.join(SCHEMA_DIR, "init_postgres.sql")


def get_db():
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ.get("DB_USER", "geo_app"),
        password=os.environ.get("DB_PASSWORD", "change-this-password"),
        dbname=os.environ.get("DB_NAME", "geo_engine"),
        connect_timeout=10,
    )


def run_schema():
    """执行 PostgreSQL 初始化脚本（幂等：CREATE TABLE IF NOT EXISTS）"""
    if not os.path.exists(PG_INIT_FILE):
        log.error("Schema 文件不存在: %s", PG_INIT_FILE)
        return 0

    cnx = get_db()
    cnx.autocommit = True
    cursor = cnx.cursor()
    try:
        sql = open(PG_INIT_FILE, encoding="utf-8").read()
        cursor.execute(sql)
        log.info("✅ init_postgres.sql 已应用")
        return 1
    except Exception as e:
        log.warning("⚠️ schema 执行: %s", e)
        return 0
    finally:
        cursor.close()
        cnx.close()


def seed_keywords():
    """导入种子关键词（幂等：ON CONFLICT DO NOTHING）"""
    if not os.path.exists(SEED_FILE):
        log.warning("种子文件不存在: %s", SEED_FILE)
        return 0

    try:
        seeds = json.loads(open(SEED_FILE, encoding="utf-8").read())
    except Exception as e:
        log.error("读取种子文件失败: %s", e)
        return 0

    cnx = get_db()
    cursor = cnx.cursor()
    inserted = 0

    for item in seeds:
        keyword = item.get("keyword", "").strip()
        if not keyword:
            continue
        vol = item.get("search_volume", 0)
        diff = item.get("difficulty", 20)
        try:
            cursor.execute(
                "INSERT INTO geo_keywords (keyword, search_volume, difficulty) "
                "VALUES (%s, %s, %s) ON CONFLICT (keyword) DO NOTHING",
                (keyword, vol, diff),
            )
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            log.warning("关键词 '%s' 导入失败: %s", keyword, e)

    cnx.commit()
    cursor.close()
    cnx.close()

    if inserted > 0:
        log.info("✅ 导入 %d 个种子关键词", inserted)
    return inserted


def check_llm_configured() -> bool:
    api_key = (
        os.environ.get("GEO_LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or ""
    )
    return len(api_key) > 10


def count_keywords() -> int:
    try:
        cnx = get_db()
        cursor = cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM geo_keywords")
        count = cursor.fetchone()[0] or 0
        cursor.close()
        cnx.close()
        return count
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="强制重建（危险）")
    args = parser.parse_args()

    log.info("=" * 50)
    log.info("  gitgeo 项目初始化 (PostgreSQL)")
    log.info("=" * 50)

    # 1. 等 PostgreSQL 就绪
    for attempt in range(30):
        try:
            cnx = get_db()
            cur = cnx.cursor()
            cur.execute("SELECT 1")
            cur.close()
            cnx.close()
            log.info("✅ PostgreSQL 连接成功")
            break
        except Exception:
            if attempt == 0:
                log.info("⏳ 等待 PostgreSQL 就绪...")
            if attempt >= 29:
                log.error("❌ PostgreSQL 连接超时")
                sys.exit(1)
            import time
            time.sleep(2)

    if args.reset:
        log.warning("⚠️ 重置模式：删除所有表...")
        cnx = get_db()
        cnx.autocommit = True
        cursor = cnx.cursor()
        tables = [
            "geo_capability_spec_sources", "geo_capability_specs",
            "geo_capability_sources", "geo_capability_profiles",
            "geo_job_steps", "geo_job_runs",
            "geo_probe_results", "geo_keyword_feedback",
            "geo_links", "geo_keywords", "article_publications", "geo_articles",
        ]
        for t in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
        cursor.execute("DROP TYPE IF EXISTS metric_type_enum CASCADE")
        cursor.execute("DROP TYPE IF EXISTS claim_level_enum CASCADE")
        cursor.close()
        cnx.close()
        log.info("✅ 旧表已清除")

    # 2. 建表
    log.info("📦 创建数据库表...")
    schema_count = run_schema()
    log.info("✅ Schema 已应用" if schema_count else "⚠️ Schema 执行异常")

    # 3. 种子
    log.info("🌱 导入种子关键词...")
    kw_count = count_keywords()
    if kw_count == 0:
        seed_keywords()
    else:
        log.info("✅ 已有 %d 个关键词（跳过种子导入）", kw_count)

    # 4. 检查 LLM
    llm_ok = check_llm_configured()
    if llm_ok:
        log.info("✅ LLM API Key 已配置")
    else:
        log.warning("⚠️ LLM API Key 未配置！")
        log.info("   export GEO_LLM_API_KEY=sk-xxx")
        log.info("   export GEO_LLM_BASE_URL=https://api.deepseek.com")
        log.info("   export GEO_LLM_MODEL=deepseek-v4-pro")

    # 5. 就绪
    log.info("=" * 50)
    log.info("  🎉 gitgeo 初始化完成！(PostgreSQL)")
    log.info("  📊 关键词: %d 个", count_keywords())
    log.info("  🤖 LLM: %s", "已配置 ✅" if llm_ok else "未配置 ⚠️")
    log.info("  🌐 Backend API: http://localhost:8001/api/v1")
    log.info("  📋 Dashboard: http://localhost:8503")
    log.info("=" * 50)


if __name__ == "__main__":
    main()
