"""
GEO 知识引擎 — 批量生产入口 (v3.0)
===================================
唯一入口文件。从 geo_keywords 表消费关键词，逐篇生成文章。

核心流程（每个关键词）：
    采集 → 结构化 → 生成 → 质检 → 返修(×3) → 下一篇

使用方法：
    # 本地运行
    python batch_generator.py

    # 后台运行（阿里云 / 服务器）
    nohup python -u batch_generator.py > batch.log 2>&1 &

环境变量（.env 文件）：
    DEEPSEEK_API_KEY  —  DeepSeek / OpenAI 兼容 API 密钥
    DB_HOST           —  MySQL 数据库地址（本地用 localhost）
    DB_USER           —  数据库用户
    DB_PASSWORD       —  数据库密码
    DB_NAME           —  数据库名称
"""

import os
import gc
import time
import json
import logging
from datetime import datetime, timedelta

# ─── 禁用 OpenTelemetry（防止 Python 3.13 导入卡死）───
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("MYSQL_CONNECTOR_PYTHON_TELEMETRY", "0")

from dotenv import load_dotenv
from crewai import Crew
from langchain_openai import ChatOpenAI

from core.agents import GeoAgents
from core.tasks import GeoTasks
from core.db_manager import db_manager
from core.quality_checker import QualityChecker
from core.auto_fixer import AutoFixer
from core.linker import AutoLinker
from core.budget import tracker
from core.build_info import format_build_label
from core.capability_store import capability_store
from core.feedback_store import feedback_store
from core.job_store import job_store
from core.prompt_optimizer import prompt_optimizer
from core.run_state import (
    clear_current_run_id,
    clear_saved_article_result,
    pop_saved_article_result,
    set_current_run_id,
)
from core.trend_scout import TrendScout
from core.active_prober import ActiveProber


# ═══════════════════════════════════════════
#  配置区
# ═══════════════════════════════════════════

load_dotenv()

# ── LLM 配置（统一从环境变量读取，不锁定供应商）──
_GEO_LLM_API_KEY = os.environ.get("GEO_LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
_GEO_LLM_BASE_URL = os.environ.get("GEO_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com"
os.environ["OPENAI_API_KEY"] = _GEO_LLM_API_KEY
os.environ["OPENAI_API_BASE"] = _GEO_LLM_BASE_URL
os.environ["OPENAI_BASE_URL"] = _GEO_LLM_BASE_URL

MAX_REPAIR_ATTEMPTS = int(os.getenv("GEO_REPAIR_ATTEMPTS", "3"))
PASS_THRESHOLD = int(os.getenv("GEO_PASS_THRESHOLD", "80"))
COOLDOWN_SECONDS = int(os.getenv("GEO_COOLDOWN_SECONDS", "5"))
SCOUT_MAX_RETRIES = int(os.getenv("GEO_SCOUT_RETRIES", "3"))
MAX_ARTICLES = int(os.getenv("GEO_MAX_ARTICLES", "0"))              # 0 = 不设上限
DAILY_GAP_ARTICLES = int(os.getenv("GEO_DAILY_GAP_ARTICLES", "5"))
GAP_MODE_RETRY_SECONDS = int(os.getenv("GEO_GAP_RETRY_SECONDS", "3600"))
ENABLE_ACTIVE_PROBING = os.getenv("GEO_ENABLE_PROBING", "false").lower() in {"1", "true", "yes"}
ACTIVE_PROBE_PLATFORMS = [
    item.strip() for item in os.getenv("GEO_PROBE_PLATFORMS", "deepseek,kimi,doubao").split(",")
    if item.strip()
]


# ═══════════════════════════════════════════
#  日志配置
# ═══════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler("batch_generator.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("GEO")

# 抑制第三方库噪音
for lib in ("openai", "httpx", "httpcore", "urllib3"):
    logging.getLogger(lib).setLevel(logging.WARNING)


# ═══════════════════════════════════════════
#  LLM 初始化
# ═══════════════════════════════════════════

_GEO_LLM_MODEL = os.environ.get("GEO_LLM_MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-chat"
llm = ChatOpenAI(
    model=_GEO_LLM_MODEL,
    base_url=_GEO_LLM_BASE_URL,
    api_key=_GEO_LLM_API_KEY,
    temperature=0.1,
    timeout=120,
)


# ═══════════════════════════════════════════
#  数据库辅助操作
# ═══════════════════════════════════════════

def get_pending_keywords(limit: int = 1) -> list:
    """获取未处理的关键词"""
    cnx = db_manager.get_connection()
    if not cnx:
        return []
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, keyword, search_volume FROM geo_keywords "
            "WHERE target_article_id IS NULL ORDER BY id ASC LIMIT %s",
            (limit,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        cnx.close()


def get_pending_gap_keywords(limit: int = 5) -> list:
    """获取 GEO 真空词队列（高优先级自动生产关键词）"""
    cnx = db_manager.get_connection()
    if not cnx:
        return []
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, keyword, search_volume FROM geo_keywords "
            "WHERE target_article_id IS NULL AND search_volume >= %s "
            "ORDER BY created_at ASC, id ASC LIMIT %s",
            (GEO_GAP_PRIORITY, limit),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        cnx.close()


def get_article(article_id: int) -> dict | None:
    """按 ID 获取文章"""
    cnx = db_manager.get_connection()
    if not cnx:
        return None
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, slug, content_markdown, publish_status "
            "FROM geo_articles WHERE id = %s LIMIT 1",
            (article_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        cnx.close()


def enqueue_suggested_keywords(keywords: list[str], base_volume: int = GEO_GAP_PRIORITY) -> list[str]:
    """将反馈生成的衍生关键词注入队列。"""
    injected: list[str] = []
    for keyword in keywords:
        cleaned = str(keyword or "").strip()
        if not cleaned:
            continue
        if db_manager.add_keyword(cleaned, search_volume=base_volume, difficulty=25):
            injected.append(cleaned)
    return injected


def update_article(article_id: int, **fields):
    """通用文章字段更新"""
    cnx = db_manager.get_connection()
    if not cnx:
        return
    try:
        cursor = cnx.cursor()
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        cursor.execute(
            f"UPDATE geo_articles SET {set_clause} WHERE id = %s",
            (*fields.values(), article_id),
        )
        cnx.commit()
    finally:
        cursor.close()
        cnx.close()


def mark_keyword_done(keyword_id: int, article_id: int):
    """标记关键词已处理"""
    cnx = db_manager.get_connection()
    if not cnx:
        return
    try:
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE geo_keywords SET target_article_id = %s WHERE id = %s",
            (article_id, keyword_id),
        )
        cnx.commit()
    finally:
        cursor.close()
        cnx.close()


def inject_seed_keywords(limit: int = 5) -> int:
    """从 seed_topics.json 注入种子关键词"""
    try:
        with open("seed_topics.json", "r", encoding="utf-8") as f:
            seeds = json.load(f)
        added = 0
        for item in seeds:
            kw = item.get("keyword")
            if kw and db_manager.add_keyword(kw):
                added += 1
                if added >= limit:
                    break
        return added
    except Exception as e:
        log.error(f"种子注入失败: {e}")
        return 0


# ═══════════════════════════════════════════
#  核心流程
# ═══════════════════════════════════════════

def check_api_health() -> bool:
    """API 连通性检查"""
    try:
        llm.invoke("ping")
        return True
    except Exception as e:
        log.error(f"API 健康检查失败: {e}")
        return False


def run_scout(agents: GeoAgents, tasks: GeoTasks):
    """侦察循环 — 发现新关键词"""
    log.info("🕵️ 触发侦察循环...")
    scout = agents.scout_agent(llm)
    crew = Crew(agents=[scout], tasks=[tasks.scout_task(scout)], verbose=True)
    try:
        crew.kickoff()
        log.info("✅ 侦察完成")
    except Exception as e:
        log.error(f"侦察失败: {e}")


def generate_article(agents: GeoAgents, tasks: GeoTasks, keyword: str):
    """执行 采集→结构化→生成 流水线"""
    collector = agents.collector_agent(llm)
    templater = agents.templater_agent(llm)
    generator = agents.generator_agent(llm)

    capability_context = capability_store.build_context(keyword, limit=5)
    optimization_context = prompt_optimizer.build_prompt_context(keyword)
    log.info(f"🧠 组织能力上下文已加载: {keyword}")
    if optimization_context:
        log.info(f"🧭 已加载监测反馈上下文: {keyword}")

    t_collect = tasks.collect_data_task(collector, keyword, capability_context=capability_context)
    t_structure = tasks.structure_content_task(templater, context=[t_collect])
    t_write = tasks.generate_article_task(
        generator,
        context=[t_structure],
        capability_context=capability_context,
        optimization_context=optimization_context,
    )

    crew = Crew(
        agents=[collector, templater, generator],
        tasks=[t_collect, t_structure, t_write],
        verbose=True,
    )
    crew.kickoff()


def quality_loop(article: dict, job_run_id: int | None = None) -> dict:
    """
    质检→返修闭环，最多 MAX_REPAIR_ATTEMPTS 次。
    返回质检结果摘要：
        {"passed": bool, "attempts": int, "final_score": int, "failed_checks": list[str]}
    """
    checker = QualityChecker()
    fixer = AutoFixer()

    article_id = article["id"]
    title = article["title"] or ""
    content = article["content_markdown"] or ""
    last_failed: list[str] = []
    last_score = 0

    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
        step_id = job_store.start_step(
            job_run_id,
            "quality_check",
            "质量检查",
            attempt_no=attempt,
            article_id=article_id,
        )

        # ── 评分 ──
        score, report = checker.evaluate_article(title, content)
        failed = [k for k, v in report.items() if not v]
        passed = [k for k, v in report.items() if v]
        last_failed = failed
        last_score = score
        detail = {
            "score": score,
            "passed_checks": passed,
            "failed_checks": failed,
            "threshold": PASS_THRESHOLD,
        }

        log.info(
            f"📊 第 {attempt}/{MAX_REPAIR_ATTEMPTS} 次质检: {score}分 "
            f"| ✅{','.join(passed)} | ❌{','.join(failed)}"
        )

        update_article(article_id, quality_score=score)

        # ── 通过 ──
        if score >= PASS_THRESHOLD:
            update_article(article_id, publish_status=1, quality_score=score)
            job_store.finish_step(step_id, status="succeeded", article_id=article_id, detail=detail)
            log.info(f"🎉 质检通过！[{score}分] {title}")
            return {
                "passed": True,
                "attempts": attempt,
                "final_score": score,
                "failed_checks": failed,
            }

        # ── 已达上限 ──
        if attempt >= MAX_REPAIR_ATTEMPTS:
            job_store.finish_step(
                step_id,
                status="failed",
                article_id=article_id,
                error_message="quality_threshold_not_reached",
                detail=detail,
            )
            log.warning(f"💀 达到最大返修次数，放弃: [{score}分] {title}")
            return {
                "passed": False,
                "attempts": attempt,
                "final_score": score,
                "failed_checks": failed,
            }

        job_store.finish_step(
            step_id,
            status="failed",
            article_id=article_id,
            error_message="quality_threshold_not_reached",
            detail=detail,
        )

        # ── 生成返修指令 ──
        fix_prompt = fixer.generate_fix_prompt(content, report)
        if not fix_prompt:
            repair_step_id = job_store.start_step(
                job_run_id,
                "repair",
                "文章返修",
                attempt_no=attempt,
                article_id=article_id,
                detail={"reason": "fix_prompt_unavailable", "score": score},
            )
            job_store.finish_step(
                repair_step_id,
                status="failed",
                article_id=article_id,
                error_message="fix_prompt_unavailable",
            )
            log.warning("AutoFixer 未生成返修指令，跳过")
            return {
                "passed": False,
                "attempts": attempt,
                "final_score": score,
                "failed_checks": failed,
            }

        # ── LLM 执行返修 ──
        repair_step_id = job_store.start_step(
            job_run_id,
            "repair",
            "文章返修",
            attempt_no=attempt,
            article_id=article_id,
            detail={"reason": "quality_threshold_not_reached", "score": score},
        )
        log.info(f"🔧 第 {attempt} 次返修...")
        try:
            result = llm.invoke(fix_prompt)
            new_content = result.content if hasattr(result, "content") else str(result)

            # ── 记录 Token 用量（月度统计）──
            usage = getattr(result, "usage_metadata", None) or getattr(result, "response_metadata", {}).get("token_usage", {})
            in_tok  = getattr(usage, "input_tokens",  None) or (usage.get("prompt_tokens") if isinstance(usage, dict) else 0) or 0
            out_tok = getattr(usage, "output_tokens", None) or (usage.get("completion_tokens") if isinstance(usage, dict) else 0) or 0
            tracker.record(in_tok, out_tok, label=f"repair:{title[:20]}")

            if len(new_content.strip()) < 500:
                job_store.finish_step(
                    repair_step_id,
                    status="failed",
                    article_id=article_id,
                    error_message="repair_result_too_short",
                    detail={"result_length": len(new_content)},
                )
                log.warning(f"返修结果过短 ({len(new_content)} 字符)，跳过")
                continue

            import hashlib
            content_hash = hashlib.md5(new_content.encode("utf-8")).hexdigest()
            update_article(article_id, content_markdown=new_content, content_hash=content_hash)
            content = new_content
            job_store.finish_step(
                repair_step_id,
                status="succeeded",
                article_id=article_id,
                detail={"result_length": len(new_content), "prompt_tokens": in_tok, "completion_tokens": out_tok},
            )
            log.info(f"✅ 返修完成，{len(new_content)} 字符")

        except Exception as e:
            job_store.finish_step(
                repair_step_id,
                status="failed",
                article_id=article_id,
                error_message=str(e),
            )
            log.error(f"LLM 返修失败: {e}")
            continue

    return {
        "passed": False,
        "attempts": MAX_REPAIR_ATTEMPTS,
        "final_score": last_score,
        "failed_checks": last_failed,
    }


def detect_trigger_mode(kw_row: dict) -> str:
    """根据关键词来源推断触发方式"""
    search_volume = int(kw_row.get("search_volume") or 0)
    return "geo_gap_auto" if search_volume >= GEO_GAP_PRIORITY else "keyword_auto"


def process_keyword(agents: GeoAgents, tasks: GeoTasks, kw_row: dict) -> bool:
    """处理单个关键词：生成 + 质检闭环"""
    keyword = kw_row["keyword"]
    kw_id = kw_row["id"]
    run_id = f"kw-{kw_id}-{int(time.time() * 1000)}"
    trigger_mode = detect_trigger_mode(kw_row)
    job_run_id = job_store.start_run(
        run_uid=run_id,
        keyword_id=int(kw_id),
        keyword=keyword,
        trigger_mode=trigger_mode,
        detail={"search_volume": int(kw_row.get("search_volume") or 0)},
    )
    log.info(f"⚡ 开始处理: {keyword}")

    clear_saved_article_result(run_id)
    set_current_run_id(run_id)
    generate_step_id = job_store.start_step(
        job_run_id,
        "generate",
        "采集-结构化-写作",
        detail={"keyword": keyword, "trigger_mode": trigger_mode},
    )
    try:
        generate_article(agents, tasks, keyword)
    except Exception as e:
        log.error(f"生成失败 [{keyword}]: {e}")
        job_store.finish_step(generate_step_id, status="failed", error_message=str(e))
        job_store.update_run(
            job_run_id,
            status="failed",
            current_step="generate",
            error_message=str(e),
            finished=True,
        )
        return False
    finally:
        clear_current_run_id()

    save_result = pop_saved_article_result(run_id)
    if not save_result:
        log.error(f"生成结束后未捕获入库结果: {keyword}")
        job_store.finish_step(
            generate_step_id,
            status="failed",
            error_message="missing_article_save_result",
        )
        job_store.update_run(
            job_run_id,
            status="failed",
            current_step="generate",
            error_message="missing_article_save_result",
            finished=True,
        )
        return False

    if not save_result.get("success"):
        reason = save_result.get("reason", "unknown")
        log.error(f"文章未成功入库 [{keyword}]: {reason}")
        job_store.finish_step(
            generate_step_id,
            status="failed",
            error_message=reason,
            detail={"save_result": save_result},
        )
        job_store.update_run(
            job_run_id,
            status="failed",
            current_step="generate",
            error_message=reason,
            detail={"save_result": save_result},
            finished=True,
        )
        return False

    article_id = save_result.get("article_id")
    if not article_id:
        log.error(f"文章入库缺少 article_id: {keyword}")
        job_store.finish_step(
            generate_step_id,
            status="failed",
            error_message="missing_article_id",
            detail={"save_result": save_result},
        )
        job_store.update_run(
            job_run_id,
            status="failed",
            current_step="generate",
            error_message="missing_article_id",
            detail={"save_result": save_result},
            finished=True,
        )
        return False

    job_store.finish_step(
        generate_step_id,
        status="succeeded",
        article_id=int(article_id),
        detail={"save_result": save_result},
    )
    job_store.update_run(job_run_id, article_id=int(article_id), current_step="quality")

    article = get_article(int(article_id))
    if not article:
        log.error(f"未找到已入库文章: {keyword} -> #{article_id}")
        job_store.update_run(
            job_run_id,
            status="failed",
            article_id=int(article_id),
            current_step="quality",
            error_message="article_not_found_after_save",
            finished=True,
        )
        return False

    log.info(
        f"🧾 已定位本次文章: #{article['id']} "
        f"{'(更新已有文章)' if save_result.get('action') == 'updated' else '(新建文章)'}"
    )

    quality_result = quality_loop(article, job_run_id=job_run_id)
    passed = bool(quality_result.get("passed"))
    final_score = int(quality_result.get("final_score") or 0)
    retry_count = max(0, int(quality_result.get("attempts") or 1) - 1)
    had_post_errors = False

    # 质检通过 → 导出 HTML → 自动内链
    if passed:
        feedback_article = get_article(int(article["id"])) or article
        feedback_step_id = job_store.start_step(
            job_run_id,
            "feedback_loop",
            "监测反馈回灌",
            article_id=article["id"],
        )
        try:
            article_profile = prompt_optimizer.analyze_article(
                keyword=keyword,
                title=str(feedback_article.get("title") or keyword),
                content=str(feedback_article.get("content_markdown") or ""),
                quality_score=final_score,
            )
            merged_feedback = {
                "feedback_labels": article_profile.get("labels") or [],
                "prompt_guidance": article_profile.get("prompt_guidance"),
                "probe_coverage_score": None,
                "suggested_keywords": article_profile.get("suggested_keywords") or [],
            }
            probe_summary = None
            probe_results: list[dict] = []
            if ENABLE_ACTIVE_PROBING:
                prober = ActiveProber()
                probe_results = prober.probe_all(keyword, platforms=ACTIVE_PROBE_PLATFORMS)
                probe_summary = prober.summarize_results(keyword, probe_results)
                merged_feedback = prompt_optimizer.merge_probe_feedback(
                    article_profile=article_profile,
                    probe_summary=probe_summary,
                )
                for result in probe_results:
                    feedback_store.save_probe_result(
                        keyword=keyword,
                        keyword_id=int(kw_id),
                        article_id=int(article["id"]),
                        platform=str(result.get("platform") or "unknown"),
                        result=result,
                    )

            feedback_store.upsert_keyword_feedback(
                keyword=keyword,
                keyword_id=int(kw_id),
                article_id=int(article["id"]),
                citation_score=float(article_profile.get("citation_score") or 0),
                probe_coverage_score=merged_feedback.get("probe_coverage_score"),
                feedback_labels=merged_feedback.get("feedback_labels"),
                article_signals=article_profile,
                probe_summary=probe_summary,
                suggested_keywords=merged_feedback.get("suggested_keywords"),
                prompt_guidance=merged_feedback.get("prompt_guidance"),
            )
            db_manager.merge_article_meta(
                int(article["id"]),
                {
                    "citation_feedback": {
                        "article_profile": article_profile,
                        "probe_summary": probe_summary,
                        "prompt_guidance": merged_feedback.get("prompt_guidance"),
                        "feedback_labels": merged_feedback.get("feedback_labels"),
                    }
                },
            )
            injected_keywords = enqueue_suggested_keywords(
                merged_feedback.get("suggested_keywords") or article_profile.get("suggested_keywords") or [],
                base_volume=GEO_GAP_PRIORITY,
            )
            job_store.finish_step(
                feedback_step_id,
                status="succeeded",
                article_id=article["id"],
                detail={
                    "citation_score": article_profile.get("citation_score"),
                    "feedback_labels": merged_feedback.get("feedback_labels"),
                    "probe_summary": probe_summary,
                    "suggested_keywords": merged_feedback.get("suggested_keywords"),
                    "injected_keywords": injected_keywords,
                },
            )
            if injected_keywords:
                log.info(f"🧬 已注入自迭代关键词: {', '.join(injected_keywords)}")
        except Exception as e:
            had_post_errors = True
            log.error(f"监测反馈回灌失败: {e}")
            job_store.finish_step(
                feedback_step_id,
                status="failed",
                article_id=article["id"],
                error_message=str(e),
            )

        # 导出 HTML 到同步目录
        export_step_id = job_store.start_step(
            job_run_id,
            "export_html",
            "导出HTML",
            article_id=article["id"],
        )
        try:
            from core.exporter import WebsiteExporter
            exporter = WebsiteExporter()
            exporter.export_article(article["id"])
            job_store.finish_step(export_step_id, status="succeeded", article_id=article["id"])
        except Exception as e:
            log.error(f"HTML 导出失败: {e}")
            had_post_errors = True
            job_store.finish_step(
                export_step_id,
                status="failed",
                article_id=article["id"],
                error_message=str(e),
            )

        link_step_id = job_store.start_step(
            job_run_id,
            "auto_link",
            "自动内链",
            article_id=article["id"],
        )
        try:
            linker = AutoLinker()
            result = linker.link_article(article["id"])
            log.info(f"🔗 内链: 出链 {result['outgoing']}, 入链 {result['incoming']}")
            job_store.finish_step(
                link_step_id,
                status="succeeded",
                article_id=article["id"],
                detail=result,
            )
        except Exception as e:
            log.error(f"内链失败: {e}")
            had_post_errors = True
            job_store.finish_step(
                link_step_id,
                status="failed",
                article_id=article["id"],
                error_message=str(e),
            )

    bind_step_id = job_store.start_step(
        job_run_id,
        "bind_keyword",
        "关键词绑定文章",
        article_id=article["id"],
    )
    try:
        mark_keyword_done(kw_id, article["id"])
        job_store.finish_step(
            bind_step_id,
            status="succeeded",
            article_id=article["id"],
            detail={"keyword_id": int(kw_id), "article_id": int(article["id"])},
        )
    except Exception as e:
        log.error(f"关键词绑定失败: {e}")
        had_post_errors = True
        job_store.finish_step(
            bind_step_id,
            status="failed",
            article_id=article["id"],
            error_message=str(e),
        )

    run_status = "succeeded" if passed and not had_post_errors else "partial" if passed else "failed"
    run_error = None if run_status == "succeeded" else "post_process_failed" if passed else "quality_threshold_not_reached"
    job_store.update_run(
        job_run_id,
        status=run_status,
        article_id=int(article["id"]),
        current_step="done",
        retry_count=retry_count,
        error_message=run_error,
        detail={
            "save_action": save_result.get("action"),
            "quality_passed": passed,
            "quality_score": final_score,
            "failed_checks": quality_result.get("failed_checks") or [],
        },
        finished=True,
    )
    return passed


def ensure_pending_keywords(agents: GeoAgents, tasks: GeoTasks) -> list:
    """确保有待处理关键词（侦察→种子注入→退出）"""
    pending = get_pending_keywords()
    if pending:
        return pending

    # 尝试侦察
    for i in range(SCOUT_MAX_RETRIES):
        log.info(f"💤 无关键词，侦察第 {i+1}/{SCOUT_MAX_RETRIES} 次...")
        try:
            run_scout(agents, tasks)
            pending = get_pending_keywords()
            if pending:
                return pending
        except Exception as e:
            log.error(f"侦察异常: {e}")
        time.sleep(10 * (i + 1))

    # 尝试种子注入
    log.info("🌱 侦察无果，注入种子关键词...")
    if inject_seed_keywords() > 0:
        return get_pending_keywords()

    return []


def get_total_articles() -> int:
    """查询数据库当前文章总数"""
    cnx = db_manager.get_connection()
    if not cnx:
        return 0
    try:
        cursor = cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM geo_articles")
        return cursor.fetchone()[0] or 0
    finally:
        cursor.close()
        cnx.close()


def get_today_gap_article_count() -> int:
    """统计今天已自动生成的 GEO 真空词文章数"""
    cnx = db_manager.get_connection()
    if not cnx:
        return 0
    try:
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT a.id) "
            "FROM geo_articles a "
            "JOIN geo_keywords k ON k.target_article_id = a.id "
            "WHERE k.search_volume >= %s AND DATE(a.created_at) = CURDATE()",
            (GEO_GAP_PRIORITY,),
        )
        result = cursor.fetchone()
        return int(result[0] or 0) if result else 0
    finally:
        cursor.close()
        cnx.close()


def sleep_until_next_gap_window():
    """今日 quota 完成后，休眠到次日 00:05。"""
    now = datetime.now()
    next_run = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    seconds = max(300, int((next_run - now).total_seconds()))
    hours = round(seconds / 3600, 2)
    log.info(f"🌙 今日 GEO 真空词 quota 已完成，休眠至次日窗口（约 {hours}h）")
    time.sleep(seconds)


def run_trend_scout(max_keywords: int = 10) -> list[str]:
    """调用 TrendScout 发现新热词并注入关键词队列，返回新增词列表"""
    try:
        scout = TrendScout(max_keywords=max_keywords)
        new_kws = scout.run()
        return new_kws
    except Exception as e:
        log.error(f"TrendScout 异常: {e}")
        return []


# ═══════════════════════════════════════════
#  主循环
# ═══════════════════════════════════════════

def main():
    """主循环 — 增量热点驱动生产模式"""
    log.info("GEO 知识引擎 v4.0 启动（增量模式）")
    log.info(f"   构建版本: {format_build_label()}")
    if job_store.ensure_schema():
        log.info("   运行记录仓库: 已就绪")
    else:
        log.warning("   运行记录仓库: 初始化失败，将仅保留日志追踪")
    if feedback_store.ensure_schema():
        log.info("   监测反馈仓库: 已就绪")
    else:
        log.warning("   监测反馈仓库: 初始化失败，将跳过 Prompt 自迭代持久化")
    if capability_store.ensure_seed_data():
        log.info("   深亚工艺能力仓库: 已就绪")
    else:
        log.warning("   深亚工艺能力仓库: 初始化失败，将回退为本地 JSON 上下文")
    log.info(
        f"   基准文章量: {MAX_ARTICLES} 篇 | "
        f"日真空词产能: {DAILY_GAP_ARTICLES} 篇 | "
        f"{tracker.monthly_summary()}"
    )

    if not check_api_health():
        log.critical("❌ API 连通性检查失败，退出。")
        return

    agents = GeoAgents()
    tasks = GeoTasks()

    total_success, total_failed = 0, 0

    while True:
        gc.collect()

        # ── 120 篇后：切换到 GEO 真空词自动生产模式 ──
        total = get_total_articles()
        if total >= MAX_ARTICLES:
            today_gap_count = get_today_gap_article_count()
            remaining = DAILY_GAP_ARTICLES - today_gap_count
            log.info(
                f"🎯 已有 {total} 篇文章（基准 {MAX_ARTICLES}）。"
                f"进入 GEO 真空词自动生产模式，今日进度 {today_gap_count}/{DAILY_GAP_ARTICLES}。"
            )

            if remaining <= 0:
                sleep_until_next_gap_window()
                continue

            pending_gap = get_pending_gap_keywords(limit=remaining)
            if len(pending_gap) < remaining:
                scout_target = max(remaining * 2, DAILY_GAP_ARTICLES)
                new_kws = run_trend_scout(max_keywords=scout_target)
                if new_kws:
                    log.info(f"🔥 捕获并入库 {len(new_kws)} 个 GEO 真空词。")
                else:
                    log.info("💤 暂未发现新的 GEO 真空词。")
                pending_gap = get_pending_gap_keywords(limit=remaining)

            if not pending_gap:
                log.info(f"💤 当前无可生产的 GEO 真空词，{GAP_MODE_RETRY_SECONDS // 60} 分钟后重试。")
                time.sleep(GAP_MODE_RETRY_SECONDS)
                continue

            for kw in pending_gap[:remaining]:
                success = process_keyword(agents, tasks, kw)
                if success:
                    total_success += 1
                else:
                    total_failed += 1

                log.info(f"累计 | 成功: {total_success} | 失败: {total_failed} | {tracker.monthly_summary()}")
                time.sleep(COOLDOWN_SECONDS)

            continue


        pending = ensure_pending_keywords(agents, tasks)
        if not pending:
            log.error("所有关键词来源耗尽，休眠 5 分钟...")
            time.sleep(300)
            continue

        kw = pending[0]
        success = process_keyword(agents, tasks, kw)

        if success:
            total_success += 1
        else:
            total_failed += 1

        log.info(f"累计 | 成功: {total_success} | 失败: {total_failed} | {tracker.monthly_summary()}")
        time.sleep(COOLDOWN_SECONDS)


if __name__ == "__main__":
    main()
