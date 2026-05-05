#!/usr/bin/env python3
"""
gitgeo 项目初始化脚本
=====================
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

SCHEMA_FILES = [
    "schema.sql",
    "feedback_schema.sql",
    "job_runtime_schema.sql",
    "pcb_capability_schema.sql",
]


def get_db():
    import mysql.connector
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "mysql_db"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "root_password"),
        database=os.environ.get("DB_NAME", "geo_knowledge_engine"),
        connection_timeout=10,
        autocommit=True,
    )


def run_schemas():
    """执行所有 schema 文件（幂等：CREATE TABLE IF NOT EXISTS）"""
    cnx = get_db()
    cursor = cnx.cursor()
    created = 0

    for filename in SCHEMA_FILES:
        filepath = os.path.join(SCHEMA_DIR, filename)
        if not os.path.exists(filepath):
            log.warning("跳过不存在的 schema: %s", filename)
            continue
        try:
            sql = open(filepath, encoding="utf-8").read()
            # 按分号拆分执行
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                if stmt and not stmt.startswith("--"):
                    cursor.execute(stmt)
            created += 1
            log.info("✅ %s", filename)
        except Exception as e:
            log.warning("⚠️ %s: %s", filename, e)

    cursor.close()
    cnx.close()
    return created


def seed_keywords():
    """导入种子关键词（幂等：INSERT IGNORE）"""
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
                "INSERT IGNORE INTO geo_keywords (keyword, search_volume, difficulty) VALUES (%s, %s, %s)",
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
    log.info("  gitgeo 项目初始化")
    log.info("=" * 50)

    # 1. 等 MySQL 就绪
    for attempt in range(30):
        try:
            cnx = get_db()
            cnx.ping()
            cnx.close()
            log.info("✅ MySQL 连接成功")
            break
        except Exception:
            if attempt == 0:
                log.info("⏳ 等待 MySQL 就绪...")
            if attempt >= 29:
                log.error("❌ MySQL 连接超时，请检查数据库配置")
                sys.exit(1)
            import time
            time.sleep(2)

    if args.reset:
        log.warning("⚠️ 重置模式：删除所有表...")
        cnx = get_db()
        cursor = cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS geo_capability_spec_sources")
        cursor.execute("DROP TABLE IF EXISTS geo_capability_specs")
        cursor.execute("DROP TABLE IF EXISTS geo_capability_sources")
        cursor.execute("DROP TABLE IF EXISTS geo_capability_profiles")
        cursor.execute("DROP TABLE IF EXISTS geo_job_steps")
        cursor.execute("DROP TABLE IF EXISTS geo_job_runs")
        cursor.execute("DROP TABLE IF EXISTS geo_probe_results")
        cursor.execute("DROP TABLE IF EXISTS geo_keyword_feedback")
        cursor.execute("DROP TABLE IF EXISTS geo_links")
        cursor.execute("DROP TABLE IF EXISTS geo_keywords")
        cursor.execute("DROP TABLE IF EXISTS geo_articles")
        cursor.close()
        cnx.close()
        log.info("✅ 旧表已清除")

    # 2. 建表
    log.info("📦 创建数据库表...")
    schema_count = run_schemas()
    log.info("✅ %d 个 schema 已应用", schema_count)

    # 3. 种子数据
    log.info("🌱 导入种子关键词...")
    keyword_count = count_keywords()
    if keyword_count == 0:
        seed_count = seed_keywords()
        if seed_count == 0:
            log.warning("⚠️ 没有导入任何关键词。请检查 seed_topics.json 或手动添加。")
            log.info("   手动添加: INSERT INTO geo_keywords (keyword) VALUES ('你的关键词');")
    else:
        log.info("✅ 已有 %d 个关键词（跳过种子导入）", keyword_count)

    # 4. 检查 LLM 配置
    llm_ok = check_llm_configured()
    if llm_ok:
        log.info("✅ LLM API Key 已配置")
    else:
        log.warning("⚠️ LLM API Key 未配置！请设置环境变量:")
        log.info("   export GEO_LLM_API_KEY=sk-xxx")
        log.info("   export GEO_LLM_BASE_URL=https://api.deepseek.com")
        log.info("   export GEO_LLM_MODEL=deepseek-chat")

    # 5. 就绪报告
    log.info("=" * 50)
    log.info("  🎉 gitgeo 初始化完成！")
    log.info("  📊 关键词: %d 个", count_keywords())
    log.info("  🤖 LLM: %s", "已配置 ✅" if llm_ok else "未配置 ⚠️")
    log.info("  🌐 Backend API: http://localhost:8001/api/v1")
    log.info("  📋 Dashboard: http://localhost:8503")
    log.info("=" * 50)


if __name__ == "__main__":
    main()
