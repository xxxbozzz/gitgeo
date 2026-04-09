"""
Dashboard v4.0 组件库
====================
品牌蓝 + 毛玻璃设计语言，Lucide SVG 图标（MIT）。
"""

import streamlit as st

# ─── Lucide SVG 图标 ───

ICONS = {
    "file-text": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
    "check-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>',
    "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "bar-chart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>',
    "link": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "refresh": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>',
    "trash": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>',
    "send": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    "network": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><path d="M12 12V8"/></svg>',
    "server": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/></svg>',
    "target": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "trending-up": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "eye": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>',
    "wrench": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    "recycle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/><path d="M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12"/><path d="m14 16-3 3 3 3"/><path d="M8.293 13.596 4.875 7.97l5.088.015"/><path d="m9.5 4.5 3-3-3-3"/><path d="M14.472 7.942 17.89 13.57H12.803"/></svg>',
    "upload": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>',
    "activity": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>',
    "cpu": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>',
    "layout": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>',
    "layers": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22.54 12.43-1.96-.89"/><path d="m2.58 12.37-1.04.46a1 1 0 0 0 0 1.84l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.84l-1.05-.46"/><path d="m2.58 16.87-1.04.46a1 1 0 0 0 0 1.84l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.84l-1.05-.46"/></svg>',
}


def icon(name: str) -> str:
    """返回指定名称的 SVG 图标 HTML"""
    return ICONS.get(name, "")


# ─── 主题 CSS ───

THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --brand: #2563eb;
        --brand-light: #3b82f6;
        --brand-soft: rgba(37, 99, 235, 0.10);
        --brand-glow: rgba(37, 99, 235, 0.25);

        --bg-base: #0a0e1a;
        --bg-surface: rgba(15, 20, 35, 0.75);
        --bg-elevated: rgba(22, 28, 48, 0.80);
        --bg-hover: rgba(30, 38, 60, 0.85);

        --glass-border: rgba(255, 255, 255, 0.06);
        --glass-border-hover: rgba(37, 99, 235, 0.30);
        --glass-blur: 16px;

        --text-pure: #ffffff;
        --text-primary: #f1f3f9;
        --text-secondary: #8b92a8;
        --text-muted: #545b72;

        --ok-color: #22c55e;
        --warn-color: #f59e0b;
        --err-color: #ef4444;

        --radius: 12px;
        --radius-sm: 8px;
        --radius-xs: 6px;
    }

    /* ── 全局 ── */
    .stApp {
        background: var(--bg-base) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: var(--text-primary);
    }

    /* ── 侧边栏 ── */
    [data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        backdrop-filter: blur(var(--glass-blur)) !important;
        -webkit-backdrop-filter: blur(var(--glass-blur)) !important;
        border-right: 1px solid var(--glass-border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
    [data-testid="stSidebar"] .stRadio label:hover { color: var(--text-primary) !important; }

    /* ── 标题 ── */
    h1, h2, h3, h4 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    h1 { font-size: 1.65rem !important; }
    h2 { font-size: 1.15rem !important; margin-top: 1.2rem !important; }

    /* ── 图标对齐 ── */
    svg.ic {
        vertical-align: middle;
        flex-shrink: 0;
    }

    /* ── 通用面板 (覆盖 st.markdown) ── */
    .glass-panel {
        background: var(--bg-surface);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 24px;
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        margin-top: 12px;
    }

    /* ── KPI 卡片 ── */
    .kpi-card {
        background: var(--bg-surface);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 20px 18px;
        text-align: left;
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100%;
    }
    .kpi-card:hover {
        border-color: var(--glass-border-hover);
        box-shadow: 0 0 20px var(--brand-soft);
    }
    .kpi-icon { color: var(--brand-light); margin-bottom: 10px; opacity: 0.8; }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    /* ── 文章行 ── */
    .article-item {
        background: var(--bg-surface);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-sm);
        padding: 14px 18px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        transition: background 0.2s ease;
    }
    .article-item:hover { background: var(--bg-hover); border-color: var(--glass-border-hover); }
    .article-title {
        font-size: 0.95rem;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .article-meta {
        font-size: 0.75rem;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
    }

    /* ── 看板列 ── */
    .board-col {
        background: var(--bg-surface);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 16px;
        min-height: 300px;
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
    }
    .board-col-header {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--glass-border);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .board-item {
        background: rgba(255, 255, 255, 0.02);
        border-radius: var(--radius-xs);
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: var(--text-primary);
        border-left: 3px solid transparent;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .board-item:hover { background: rgba(255, 255, 255, 0.05); }

    /* ── 系统状态行 ── */
    .sys-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid var(--glass-border);
        background: var(--bg-surface);
    }
    .sys-row:first-child { border-radius: var(--radius) var(--radius) 0 0; }
    .sys-row:last-child { border-radius: 0 0 var(--radius) var(--radius); border-bottom: none; }
    .sys-label { font-size: 0.85rem; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }
    .sys-value { font-size: 0.9rem; color: var(--text-primary); font-weight: 500; display: flex; align-items: center; gap: 4px; }

    /* ── 分数与其他 ── */
    .score-tag {
        padding: 4px 12px;
        border-radius: var(--radius-xs);
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        flex-shrink: 0;
        margin-left: 12px;
    }
    .score-pass { background: var(--success-soft); color: var(--ok-color); }
    .score-warn { background: var(--warning-soft); color: var(--warn-color); }
    .score-fail { background: var(--danger-soft); color: var(--err-color); }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .dot-yellow { background: var(--warn-color); box-shadow: 0 0 6px var(--warn-color); }
    .dot-green { background: var(--ok-color); box-shadow: 0 0 6px var(--ok-color); }
    .dot-blue { background: var(--brand); box-shadow: 0 0 6px var(--brand); }
    .status-text {
        font-size: 0.75rem;
        color: var(--text-secondary);
        display: inline-flex;
        align-items: center;
    }

    /* ── Streamlit 组件覆盖 ── */
    .stMetric {
        background: var(--bg-surface);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 16px !important;
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: var(--text-pure) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        color: var(--text-secondary) !important;
    }
    
    .stButton > button {
        background: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        backdrop-filter: blur(var(--glass-blur)) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        border-color: var(--brand) !important;
        background: var(--brand-soft) !important;
        box-shadow: 0 0 12px var(--brand-soft) !important;
    }
    
    /* 解决 Pyvis 网络图在 iframe 中白屏/边框太硬的问题 */
    div[data-testid="stVerticalBlock"] div.element-container iframe {
        border-radius: var(--radius);
        border: 1px solid var(--glass-border);
        background: var(--bg-surface);
    }
    
    /* 表格覆盖 */
    [data-testid="stDataFrame"] {
        background: var(--bg-surface);
        border-radius: var(--radius);
        padding: 10px;
    }

    /* ── 隐藏 Streamlit 默认元素 ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
"""


def inject_theme():
    """注入全局主题 CSS"""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


# ─── 可复用组件 ───

def kpi_card(icon_name: str, value, label: str):
    """渲染一个 KPI 卡片"""
    svg = icon(icon_name)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{svg}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def score_tag(score: int) -> str:
    """返回分数标签 HTML"""
    if score >= 80:
        css = "score-pass"
    elif score >= 60:
        css = "score-warn"
    else:
        css = "score-fail"
    return f'<span class="score-tag {css}">{score}</span>'


def status_dot(status: int) -> str:
    """返回状态圆点 HTML（包括 flex 居中容器）"""
    if status >= 2:
        return '<span class="status-text"><span class="status-dot dot-blue"></span>已发布</span>'
    elif status >= 1:
        return '<span class="status-text"><span class="status-dot dot-green"></span>已通过</span>'
    return '<span class="status-text"><span class="status-dot dot-yellow"></span>草稿</span>'


def article_row(title: str, score: int, status: int, date: str) -> str:
    """返回文章行 HTML"""
    return f"""
    <div class="article-item">
        <div>
            <div class="article-title">{title}</div>
            <div class="article-meta">{status_dot(status)} · {date}</div>
        </div>
        {score_tag(score)}
    </div>
    """


def board_column(header_icon: str, header_text: str, items: list[str]):
    """渲染看板列"""
    svg = icon(header_icon)
    items_html = "".join(f'<div class="board-item">{item}</div>' for item in items)
    if not items:
        items_html = '<div class="board-item" style="color:var(--text-muted);">暂无</div>'
    st.markdown(f"""
    <div class="board-col">
        <div class="board-col-header">{svg} {header_text}</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)


def sys_info_row(icon_name: str, label: str, value: str) -> str:
    """返回系统信息行 HTML"""
    svg = icon(icon_name)
    return f"""
    <div class="sys-row">
        <div class="sys-label">{svg} {label}</div>
        <div class="sys-value">{value}</div>
    </div>
    """


def section_header(text: str, icon_name: str = ""):
    """渲染段落标题（带可选图标，强制单行垂直居中）"""
    svg = icon(icon_name) if icon_name else ""
    st.markdown(
        f'<h2 style="display:flex;align-items:center;gap:8px;">{svg} {text}</h2>',
        unsafe_allow_html=True,
    )
