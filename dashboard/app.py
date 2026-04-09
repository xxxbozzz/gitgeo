"""
GEO Engine Console v4.0
=======================
通用 GEO 控制台，包含 4 个主要页面。
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import mysql.connector
import os
import sys
import time
import hashlib
import json
import tempfile

# 确保项目根目录在 sys.path（dashboard 从子目录运行时需要）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.api_client import fetch_backend_data, get_backend_api_base, post_backend_data
from dashboard.components import inject_theme, icon, kpi_card, score_tag, status_dot
from dashboard.components import article_row, board_column, sys_info_row, section_header
from core.build_info import format_build_label

BASELINE_ARTICLES = int(os.getenv("MAX_ARTICLES", "120"))
DAILY_GAP_ARTICLES = int(os.getenv("DAILY_GAP_ARTICLES", "5"))

st.set_page_config(
    page_title="GEO Engine Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════
#  数据库
# ═══════════════════════════════════════════

@st.cache_resource(ttl=60)
def get_connection():
    """缓存数据库连接，60秒过期"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root_password"),
        database=os.getenv("DB_NAME", "geo_knowledge_engine"),
        connection_timeout=5,
        autocommit=True,
    )


def query(sql: str, params=None) -> pd.DataFrame:
    """执行查询，连接断开时自动重连"""
    try:
        cnx = get_connection()
        cnx.ping(reconnect=True)
        return pd.read_sql(sql, cnx, params=params)
    except Exception as e:
        st.cache_resource.clear()
        st.error(f"数据库查询失败: {e}")
        return pd.DataFrame()


def query_value(sql: str, default=0):
    """查询单个值"""
    df = query(sql)
    if df.empty:
        return default
    return df.iloc[0, 0] if df.iloc[0, 0] is not None else default


def execute_sql(sql: str, params=None):
    """执行写操作"""
    try:
        cnx = get_connection()
        cnx.ping(reconnect=True)
        cursor = cnx.cursor()
        cursor.execute(sql, params)
        cnx.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"数据库操作失败: {e}")
        return False


def render_backend_mode_notice(errors: list[str]):
    """显示当前页面是否走后端 API。"""
    if errors:
        st.caption(
            f"当前使用数据库回退模式。Backend API: {get_backend_api_base()} "
            f"| 原因: {errors[0]}"
        )
    else:
        st.caption(f"当前使用 Backend API: {get_backend_api_base()}")


def get_overview_kpis_data():
    """优先通过 backend overview API 获取 KPI。"""
    data, error = fetch_backend_data("overview/kpis")
    if error is None and isinstance(data, dict):
        return data, error
    return {
        "articles_total": int(query_value("SELECT COUNT(*) FROM geo_articles") or 0),
        "passed_articles": int(query_value("SELECT COUNT(*) FROM geo_articles WHERE publish_status >= 1") or 0),
        "pending_keywords": int(query_value("SELECT COUNT(*) FROM geo_keywords WHERE target_article_id IS NULL") or 0),
        "average_quality_score": query_value(
            "SELECT ROUND(AVG(quality_score),1) FROM geo_articles WHERE quality_score > 0",
            default=0,
        ),
        "internal_links": int(query_value("SELECT COUNT(*) FROM geo_links") or 0),
        "latest_article_at": query_value(
            "SELECT DATE_FORMAT(MAX(created_at), '%Y-%m-%d %H:%i:%s') FROM geo_articles",
            default="--",
        ),
        "warning": None,
    }, error


def get_overview_trend_data(days: int = 7):
    """优先通过 backend overview API 获取趋势。"""
    data, error = fetch_backend_data("overview/trend", params={"days": days})
    if error is None and isinstance(data, dict):
        items = data.get("items") or []
        return pd.DataFrame(items), error
    return query(
        """
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM geo_articles
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY day
        """
    ), error


def get_overview_board_data():
    """优先通过 backend overview API 获取看板列。"""
    data, error = fetch_backend_data(
        "overview/board",
        params={"pending_limit": 5, "article_limit": 5},
    )
    if error is None and isinstance(data, dict):
        return data, error
    return {
        "pending_keywords": query(
            "SELECT id, keyword, search_volume, difficulty "
            "FROM geo_keywords WHERE target_article_id IS NULL ORDER BY id ASC LIMIT 5"
        ).to_dict(orient="records"),
        "draft_articles": query(
            "SELECT id, title, slug, quality_score, publish_status, created_at, updated_at "
            "FROM geo_articles WHERE publish_status = 0 ORDER BY created_at DESC LIMIT 5"
        ).to_dict(orient="records"),
        "ready_articles": query(
            "SELECT id, title, slug, quality_score, publish_status, created_at, updated_at "
            "FROM geo_articles WHERE publish_status >= 1 ORDER BY created_at DESC LIMIT 5"
        ).to_dict(orient="records"),
        "warning": None,
    }, error


def get_latest_articles_data(limit: int = 8):
    """优先通过 backend overview API 获取最新文章。"""
    data, error = fetch_backend_data("overview/latest-articles", params={"limit": limit})
    if error is None and isinstance(data, dict):
        return data.get("items") or [], error
    return query(
        "SELECT id, title, quality_score, publish_status, created_at "
        "FROM geo_articles ORDER BY created_at DESC LIMIT %s",
        params=(limit,),
    ).to_dict(orient="records"), error


def get_articles_data(status_filter: str, score_filter: int):
    """优先通过 backend articles API 获取文章列表。"""
    status_map = {
        "全部": None,
        "草稿": "draft",
        "已通过": "approved",
        "已发布": "published",
    }
    params = {
        "limit": 500,
        "offset": 0,
        "min_score": int(score_filter or 0),
    }
    status_value = status_map.get(status_filter)
    if status_value:
        params["status"] = status_value

    data, error = fetch_backend_data("articles", params=params)
    if error is None and isinstance(data, dict):
        items = data.get("items") or []
        return pd.DataFrame(items), error

    articles = query(
        "SELECT id, title, slug, quality_score, publish_status, created_at "
        "FROM geo_articles ORDER BY created_at DESC"
    )
    if articles.empty:
        return articles, error

    filtered = articles.copy()
    if status_filter == "草稿":
        filtered = filtered[filtered["publish_status"] == 0]
    elif status_filter == "已通过":
        filtered = filtered[filtered["publish_status"] == 1]
    elif status_filter == "已发布":
        filtered = filtered[filtered["publish_status"] >= 2]
    if score_filter > 0:
        filtered = filtered[filtered["quality_score"] >= score_filter]
    return filtered, error


def get_articles_summary_data():
    """优先通过 backend articles summary API 获取状态统计。"""
    data, error = fetch_backend_data("articles/summary")
    if error is None and isinstance(data, dict):
        return data, error
    return {
        "total_articles": int(query_value("SELECT COUNT(*) FROM geo_articles") or 0),
        "draft_articles": int(query_value("SELECT COUNT(*) FROM geo_articles WHERE publish_status = 0") or 0),
        "approved_articles": int(query_value("SELECT COUNT(*) FROM geo_articles WHERE publish_status = 1") or 0),
        "published_articles": int(query_value("SELECT COUNT(*) FROM geo_articles WHERE publish_status >= 2") or 0),
        "average_quality_score": query_value(
            "SELECT ROUND(AVG(quality_score),1) FROM geo_articles WHERE quality_score > 0",
            default=0,
        ),
        "warning": None,
    }, error


def get_article_detail_data(article_id: int):
    """优先通过 backend articles API 获取文章详情。"""
    data, error = fetch_backend_data(f"articles/{int(article_id)}")
    if error is None and isinstance(data, dict) and data.get("article"):
        return data["article"], error

    detail = query(
        """
        SELECT id, title, slug, content_markdown, quality_score, publish_status, created_at
        FROM geo_articles
        WHERE id = %s
        """,
        params=(int(article_id),),
    )
    if detail.empty:
        return None, error
    row = detail.iloc[0].to_dict()
    return row, error


def get_system_status_data():
    """优先通过 backend system API 获取系统状态。"""
    data, error = fetch_backend_data("system/status")
    if error is None and isinstance(data, dict):
        return data, error

    try:
        query_value("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "environment": os.getenv("APP_ENV", "Production"),
        "debug": False,
        "database": db_status,
        "llm_api_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")),
        "build": format_build_label(),
    }, error


def run_article_action(path: str, payload: dict | None = None):
    """执行后端文章写操作。"""
    return post_backend_data(path, json=payload or {})


# ═══════════════════════════════════════════
#  注入主题 + 侧边栏
# ═══════════════════════════════════════════

inject_theme()

st.sidebar.markdown(f"""
<div style="padding:12px 0 8px 0;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        {icon('layers')}
        <span style="font-size:1.05rem;font-weight:600;color:#f1f3f9 !important;">GEO 控制台</span>
    </div>
    <div style="font-size:0.7rem;color:#545b72 !important;">v4.0 · Generic Edition</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "导航",
    ["总览", "内容管理", "知识图谱", "系统状态"],
    label_visibility="collapsed",
)

if st.sidebar.button("刷新数据"):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 GEO Engine")
st.sidebar.caption(f"Build: {format_build_label()}")
auto_refresh_overview = st.sidebar.checkbox("总览自动刷新", value=True)


# ═══════════════════════════════════════════
#  页面 1: 总览
# ═══════════════════════════════════════════

if page == "总览":
    if auto_refresh_overview:
        components.html(
            """
            <script>
            setTimeout(function () {
              window.parent.location.reload();
            }, 60000);
            </script>
            """,
            height=0,
        )

    st.markdown('<div class="page-title">数据总览</div>', unsafe_allow_html=True)
    st.caption(f"页面刷新时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    overview_errors = []

    # ── KPI 卡片 ──
    kpis_payload, kpis_error = get_overview_kpis_data()
    if kpis_error:
        overview_errors.append(kpis_error)
    total = int(kpis_payload.get("articles_total") or 0)
    passed = int(kpis_payload.get("passed_articles") or 0)
    pending_kw = int(kpis_payload.get("pending_keywords") or 0)
    avg_score = kpis_payload.get("average_quality_score") or 0
    links = int(kpis_payload.get("internal_links") or 0)
    latest_article_time = kpis_payload.get("latest_article_at") or "--"

    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
    cols = st.columns(6)
    kpi_data = [
        ("file-text", total, "文章总数"),
        ("check-circle", passed, "质检通过"),
        ("clock", pending_kw, "待处理词"),
        ("target", avg_score, "平均质量分"),
        ("link", links, "内链关系"),
        ("calendar", latest_article_time, "最新入库时间"),
    ]
    for col, (ic, val, label) in zip(cols, kpi_data):
        with col:
            kpi_card(ic, val, label)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 7日趋势图 & 发文统计 ──
    st.markdown('<div class="grid-2-1">', unsafe_allow_html=True)
    col_chart, col_board = st.columns([3, 2], gap="large")

    with col_chart:
        st.markdown(f'<div class="sub-title">{icon("trending-up")} 7日产出趋势</div>', unsafe_allow_html=True)

        trend_df, trend_error = get_overview_trend_data(days=7)
        if trend_error:
            overview_errors.append(trend_error)

        if not trend_df.empty:
            import plotly.graph_objects as go

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_df["day"],
                y=trend_df["count"],
                mode="lines+markers",
                line=dict(color="#3b82f6", width=2.5),
                marker=dict(size=7, color="#2563eb"),
                fill="tozeroy",
                fillcolor="rgba(37, 99, 235, 0.08)",
                hovertemplate="%{x|%m-%d}<br>产出 %{y} 篇<extra></extra>",
            ))
            fig.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False,
                    color="#545b72",
                    tickformat="%m-%d",
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.04)",
                    color="#545b72",
                    dtick=1,
                ),
                font=dict(family="Inter, sans-serif", size=12),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("暂无近7日数据。")

        # ── 发文统计 ──
        st.markdown(f'<div class="sub-title" style="margin-top:24px;">{icon("bar-chart")} 发文统计</div>', unsafe_allow_html=True)
        article_summary, summary_error = get_articles_summary_data()
        if summary_error:
            overview_errors.append(summary_error)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("草稿", int(article_summary.get("draft_articles") or 0))
        with c2:
            st.metric("质检通过", int(article_summary.get("approved_articles") or 0))
        with c3:
            st.metric("已发布", int(article_summary.get("published_articles") or 0))

    # ── 生产看板 ──
    with col_board:
        st.markdown(f'<div class="sub-title">{icon("layout")} 生产看板</div>', unsafe_allow_html=True)

        board_payload, board_error = get_overview_board_data()
        if board_error:
            overview_errors.append(board_error)
        pending_items = board_payload.get("pending_keywords") or []
        draft_items = board_payload.get("draft_articles") or []
        ready_items = board_payload.get("ready_articles") or []

        board_column("clock", "待处理词", [str(item.get("keyword") or "") for item in pending_items])
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        board_column("wrench", "质检与修复", [
            (str(item.get("title") or "")[:22] + "..." if len(str(item.get("title") or "")) > 22 else str(item.get("title") or ""))
            for item in draft_items
        ])
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        board_column("check-circle", "最新入库", [
            (str(item.get("title") or "")[:22] + "..." if len(str(item.get("title") or "")) > 22 else str(item.get("title") or ""))
            for item in ready_items
        ])

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 最新文章 ──
    st.markdown(f'<div class="sub-title" style="margin-top:24px;">{icon("file-text")} 最新入库记录</div>', unsafe_allow_html=True)

    recent_items, latest_error = get_latest_articles_data(limit=8)
    if latest_error:
        overview_errors.append(latest_error)
    render_backend_mode_notice(overview_errors)
    if recent_items:
        rows_html = ""
        for item in recent_items:
            score = item.get("quality_score") or 0
            title_text = str(item.get("title") or "")
            title = title_text[:50] + "..." if len(title_text) > 50 else title_text
            date_str = str(item.get("created_at") or "")[:16]
            rows_html += article_row(title, int(score), int(item.get("publish_status") or 0), date_str)
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.info("暂无文章。")


# ═══════════════════════════════════════════
#  页面 2: 内容管理
# ═══════════════════════════════════════════

elif page == "内容管理":
    st.markdown('<div class="page-title">内容管理</div>', unsafe_allow_html=True)

    # ── 筛选栏 ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title" style="margin-top:0;">{icon("search")} 筛选条件</div>', unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        status_filter = st.selectbox("状态", ["全部", "草稿", "已通过", "已发布"], label_visibility="collapsed")
    with col_f2:
        score_filter = st.slider("最低分数", 0, 100, 0, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    articles, articles_error = get_articles_data(status_filter, score_filter)

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title" style="margin-top:0;">{icon("database")} 文章列表</div>', unsafe_allow_html=True)
    render_backend_mode_notice([articles_error] if articles_error else [])

    if articles.empty:
        st.info("暂无文章。")
    else:
        st.dataframe(
            articles[["id", "title", "quality_score", "publish_status", "created_at"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "ID",
                "title": "标题",
                "quality_score": st.column_config.ProgressColumn("质量分", min_value=0, max_value=100, format="%d"),
                "publish_status": "状态",
                "created_at": "创建时间",
            },
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 文章操作区 ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title" style="margin-top:0;">{icon("wrench")} 文章操作</div>', unsafe_allow_html=True)

    col_id, col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1.5, 1, 1, 1, 1])
    
    with col_id:
        article_id = st.number_input("输入文章 ID", min_value=1, step=1, label_visibility="collapsed")

    with col_btn1:
        if st.button("预览全文", use_container_width=True):
            st.session_state["action"] = "preview"
            st.session_state["action_id"] = int(article_id)

    with col_btn2:
        if st.button("重新修复", use_container_width=True):
            st.session_state["action"] = "refix"
            st.session_state["action_id"] = int(article_id)

    with col_btn3:
        if st.button("回收关键词", use_container_width=True):
            st.session_state["action"] = "recycle"
            st.session_state["action_id"] = int(article_id)

    with col_btn4:
        if st.button("手动发布", use_container_width=True):
            st.session_state["action"] = "publish"
            st.session_state["action_id"] = int(article_id)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 执行操作 ──
    action = st.session_state.get("action")
    action_id = st.session_state.get("action_id")

    if action and action_id:

        # 预览全文
        if action == "preview":
            st.markdown('<div class="glass-panel" style="border-color:var(--brand-glow);">', unsafe_allow_html=True)
            st.markdown(f'<div class="sub-title" style="margin-top:0;color:var(--brand-light);">{icon("eye")} 文章预览 (ID: {action_id})</div>', unsafe_allow_html=True)
            detail, detail_error = get_article_detail_data(int(action_id))
            render_backend_mode_notice([detail_error] if detail_error else [])
            if detail:
                score = int(detail.get("quality_score") or 0)
                st.markdown(f"""
                <div class="glass-panel">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                        <h2 style="margin:0 !important;">{detail.get('title') or ''}</h2>
                        {score_tag(score)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("全文内容", expanded=True):
                    st.markdown(detail.get("content_markdown") or "（空）")
            else:
                st.warning("未找到该文章。")

        # 重新修复
        elif action == "refix":
            detail, detail_error = get_article_detail_data(int(action_id))
            render_backend_mode_notice([detail_error] if detail_error else [])
            if not detail:
                st.warning("未找到该文章。")
            else:
                st.info(f"正在修复: {detail.get('title') or ''}")

                with st.spinner("后端正在执行返修..."):
                    result, action_error = run_article_action(f"articles/{int(action_id)}/refix")

                if action_error:
                    st.error((result or {}).get("message") or action_error)
                else:
                    message = (result or {}).get("message") or "返修完成。"
                    status = (result or {}).get("status")
                    if status == "recycled_after_failed_refix":
                        st.warning(message)
                    else:
                        st.success(message)

            st.session_state["action"] = None

        # 回收关键词
        elif action == "recycle":
            detail, detail_error = get_article_detail_data(int(action_id))
            render_backend_mode_notice([detail_error] if detail_error else [])
            if not detail:
                st.warning("未找到该文章。")
            else:
                with st.spinner("后端正在回收关键词并删除文章..."):
                    result, action_error = run_article_action(f"articles/{int(action_id)}/recycle")
                if action_error:
                    st.error((result or {}).get("message") or action_error)
                else:
                    st.success((result or {}).get("message") or f"文章 #{action_id} 已回收。")

            st.session_state["action"] = None

        # 手动发布 → 选择平台 → 自动推送
        elif action == "publish":
            detail, detail_error = get_article_detail_data(int(action_id))
            render_backend_mode_notice([detail_error] if detail_error else [])
            if not detail:
                st.warning("未找到该文章。")
                st.session_state["action"] = None
            else:
                score = int(detail.get("quality_score") or 0)
                title = str(detail.get("title") or "")

                st.markdown('<div class="glass-panel" style="border-color:var(--brand-glow);">', unsafe_allow_html=True)
                st.markdown(f'<div class="sub-title" style="margin-top:0;color:var(--brand-light);">{icon("send")} 发布文章 (ID: {action_id})</div>', unsafe_allow_html=True)

                # 文章信息展示
                st.markdown(f"""
                <div style="padding:12px 16px;background:rgba(37,99,235,0.06);border-radius:8px;margin-bottom:16px;">
                    <div style="font-size:1rem;font-weight:600;color:var(--text-primary);margin-bottom:4px;">{title[:60]}</div>
                    <div style="font-size:0.8rem;color:var(--text-secondary);">
                        质量分: {score_tag(score)} &nbsp;|&nbsp; 状态: {'已通过' if detail.get('publish_status') == 1 else '草稿' if detail.get('publish_status') == 0 else '已发布'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 平台选择
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    pub_zhihu = st.checkbox("📘 知乎专栏", value=True, key="pub_zhihu")
                with col_p2:
                    pub_wechat = st.checkbox("💚 微信公众号", value=True, key="pub_wechat")

                # 模式选择
                pub_mode = st.radio(
                    "发布模式",
                    ["保存到草稿箱（推荐）", "直接发布（立即上线）"],
                    horizontal=True,
                    key="pub_mode",
                )
                is_live = "直接" in pub_mode

                if is_live:
                    st.warning("⚠️ 直接发布后文章会立即上线，微信公众号每天仅可群发 1 次。")

                # 确认发布按钮
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    confirm = st.button("✅ 确认发布", use_container_width=True, type="primary")
                with col_cancel:
                    cancel = st.button("取消", use_container_width=True)

                if cancel:
                    st.session_state["action"] = None
                    st.rerun()

                if confirm:
                    if not pub_zhihu and not pub_wechat:
                        st.error("请至少选择一个发布平台。")
                    else:
                        selected_platforms = []
                        if pub_zhihu:
                            selected_platforms.append("zhihu")
                        if pub_wechat:
                            selected_platforms.append("wechat")

                        with st.spinner("后端正在推送文章..."):
                            result, action_error = run_article_action(
                                f"articles/{int(action_id)}/publish",
                                payload={
                                    "platforms": selected_platforms,
                                    "go_live": is_live,
                                },
                            )

                        # ── 显示结果 ──
                        platform_name_map = {"zhihu": "知乎", "wechat": "微信"}
                        for item in (result or {}).get("results", []):
                            platform = platform_name_map.get(item.get("platform"), item.get("platform"))
                            message = item.get("message") or ""
                            if item.get("success"):
                                st.success(f"**{platform}**: {message}")
                            else:
                                st.error(f"**{platform}**: {message}")

                        if action_error and not (result or {}).get("results"):
                            st.error((result or {}).get("message") or action_error)
                        elif not action_error:
                            st.success((result or {}).get("message") or "发布完成。")

                        st.session_state["action"] = None

                st.markdown('</div>', unsafe_allow_html=True)


    # ── GEO 真空词自动生产 ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title" style="margin-top:0;">{icon("target")} GEO 真空词自动生产</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">'
        f'达到 {BASELINE_ARTICLES} 篇后，系统每天自动生产 {DAILY_GAP_ARTICLES} 篇 AI 知识真空关键词文章，'
        'Dashboard 仅展示队列与进度，不再进行人工筛选生产。</p>',
        unsafe_allow_html=True,
    )

    total_articles = int(query_value("SELECT COUNT(*) FROM geo_articles", default=0) or 0)
    today_gap_generated = int(query_value(
        "SELECT COUNT(DISTINCT a.id) "
        "FROM geo_articles a "
        "JOIN geo_keywords k ON k.target_article_id = a.id "
        "WHERE k.search_volume >= 9999 AND DATE(a.created_at) = CURDATE()",
        default=0,
    ) or 0)
    pending_gap_total = int(query_value(
        "SELECT COUNT(*) FROM geo_keywords "
        "WHERE target_article_id IS NULL AND search_volume >= 9999",
        default=0,
    ) or 0)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("当前文章总数", total_articles)
    with c2:
        st.metric("今日真空词产出", today_gap_generated)
    with c3:
        st.metric("待生产真空词", pending_gap_total)

    if total_articles < BASELINE_ARTICLES:
        st.info(
            f"当前仍处于基础内容建设阶段。达到 {BASELINE_ARTICLES} 篇后，"
            f"系统会自动切换为“每日 {DAILY_GAP_ARTICLES} 篇真空词文章”的生产模式。"
        )

    # 展示自动队列（只读）
    pending_kws = query(
        "SELECT keyword, created_at FROM geo_keywords "
        "WHERE target_article_id IS NULL AND search_volume >= 9999 "
        "ORDER BY created_at ASC LIMIT 5"
    )

    if not pending_kws.empty:
        st.markdown(
            '<p style="color:var(--text-secondary);font-size:0.85rem;margin-top:16px;margin-bottom:8px;">'
            f'自动生产队列（前 {len(pending_kws)} 个）：</p>',
            unsafe_allow_html=True,
        )
        for _, kw_row in pending_kws.iterrows():
            kw_text = kw_row["keyword"]
            created_at = str(kw_row["created_at"])[:16] if kw_row["created_at"] else ""
            col_kw, col_meta = st.columns([4, 2])
            with col_kw:
                st.markdown(
                    f'<div style="padding:8px 0;color:var(--text-primary);font-size:0.95rem;">'
                    f'🎯 {kw_text}</div>',
                    unsafe_allow_html=True,
                )
            with col_meta:
                st.markdown(
                    f'<div style="padding:8px 0;color:var(--text-secondary);font-size:0.82rem;text-align:right;">'
                    f'入队时间: {created_at}</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("当前没有待自动生产的 GEO 真空词，系统会按日配额自动侦察并补充。")

    st.markdown('</div>', unsafe_allow_html=True)



# ═══════════════════════════════════════════
#  页面 3: 知识图谱
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
#  页面 3: 知识图谱
# ═══════════════════════════════════════════

elif page == "知识图谱":
    st.markdown('<div class="page-title">知识图谱</div>', unsafe_allow_html=True)

    link_count = query_value("SELECT COUNT(*) FROM geo_links")
    article_count = query_value(
        "SELECT COUNT(DISTINCT id) FROM geo_articles WHERE id IN "
        "(SELECT source_id FROM geo_links UNION SELECT target_id FROM geo_links)"
    )

    st.markdown('<div class="grid-2">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        kpi_card("link", link_count, "内链总数")
    with c2:
        kpi_card("network", article_count, "关联文章数")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-panel" style="margin-top:24px;">', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title" style="margin-top:0;">{icon("network")} 交互式网络图</div>', unsafe_allow_html=True)

    links_df = query("""
        SELECT l.source_id, l.target_id, l.anchor_text,
               a1.title as source_title, a2.title as target_title
        FROM geo_links l
        JOIN geo_articles a1 ON l.source_id = a1.id
        JOIN geo_articles a2 ON l.target_id = a2.id
        ORDER BY l.created_at DESC LIMIT 200
    """)

    if not links_df.empty:
        try:
            from pyvis.network import Network
            import tempfile
            import streamlit.components.v1 as components

            net = Network(
                height="540px",
                width="100%",
                bgcolor="transparent",
                font_color="#f1f3f9",
                directed=True,
                notebook=False,
                cdn_resources="remote",
            )
            net.set_options("""
            {
                "nodes": {
                    "shape": "dot",
                    "size": 14,
                    "font": {"size": 11, "color": "#8b92a8", "face": "Inter, sans-serif"},
                    "color": {
                        "background": "#2563eb",
                        "border": "rgba(255, 255, 255, 0.1)",
                        "highlight": {"background": "#3b82f6", "border": "#ffffff"}
                    }
                },
                "edges": {
                    "color": {"color": "rgba(255, 255, 255, 0.1)", "highlight": "#2563eb"},
                    "width": 1,
                    "smooth": {"type": "continuous"}
                },
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -4000,
                        "centralGravity": 0.3,
                        "springLength": 100,
                        "springConstant": 0.04
                    }
                }
            }
            """)

            added_nodes = set()
            for _, r in links_df.iterrows():
                sid, tid = r["source_id"], r["target_id"]
                n1, n2 = str(r["source_title"])[:20], str(r["target_title"])[:20]

                if sid not in added_nodes:
                    net.add_node(sid, label=n1, title=r["source_title"])
                    added_nodes.add(sid)
                if tid not in added_nodes:
                    net.add_node(tid, label=n2, title=r["target_title"])
                    added_nodes.add(tid)
                net.add_edge(sid, tid, title=f"锚文本: {r['anchor_text']}")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, "r", encoding="utf-8") as f:
                    html_data = f.read()

            components.html(html_data, height=560)
            os.unlink(tmp.name)

        except ImportError:
            st.warning("请安装 pyvis: `pip install pyvis` 以显示交互式图谱。")
            st.dataframe(links_df)
    else:
        st.info("暂无足够的内链关系数据。")
        
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  页面 4: 系统状态
# ═══════════════════════════════════════════

elif page == "系统状态":
    st.markdown('<div class="page-title">系统状态</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title" style="margin-top:0;">{icon("server")} 服务状态检查</div>', unsafe_allow_html=True)

    system_status, system_error = get_system_status_data()
    render_backend_mode_notice([system_error] if system_error else [])

    db_status = (
        '<span style="color:var(--ok-color);font-weight:600;">正常</span>'
        if system_status.get("database") == "ok"
        else '<span style="color:var(--err-color);font-weight:600;">异常</span>'
    )
    api_status = (
        '<span style="color:var(--ok-color);font-weight:600;">已配置</span>'
        if system_status.get("llm_api_configured")
        else '<span style="color:var(--warn-color);font-weight:600;">未配置</span>'
    )
    env_str = system_status.get("environment") or os.getenv("APP_ENV", "Production")
    build_label = system_status.get("build") or format_build_label()

    from core.budget import tracker
    budget_stats = tracker.monthly_summary()
    
    rows = [
        sys_info_row("database", "MySQL 数据库连接", db_status),
        sys_info_row("cpu", "LLM API 状态", api_status),
        sys_info_row("layers", "当前运行环境", env_str),
        sys_info_row("box", "当前 Build 版本", f'<span style="color:var(--brand-light);">{build_label}</span>'),
        sys_info_row("clock", "Token 用量统计", f'<span style="color:var(--brand-light);">{budget_stats}</span>'),
    ]
    st.markdown("".join(rows), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="sub-title" style="margin-top:24px;">{icon("shield")} AI 知识覆盖率检测 (GEO)</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-panel">
        <p style="color:var(--text-secondary);font-size:0.9rem;margin-bottom:12px;">实时追踪大型语言模型 (LLM) 对目标主题知识的回答覆盖率。由于转入按需生成模式，系统主要通过以下方式扩展知识库：</p>
        <div style="font-size:0.85rem;color:var(--text-primary);display:flex;flex-direction:column;gap:8px;">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="color:var(--brand-light);">✓</span> 挖掘用户真实痛点和行业高频长尾词
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="color:var(--brand-light);">✓</span> 识别各类 AI 平台的回答空白与证据缺口
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="color:var(--brand-light);">✓</span> 优先生成当前模型答不好的技术长文和问答
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
