#!/usr/bin/env python3
"""
知识库可视化仪表盘 (Web Dashboard)
功能: 
- 展示文章列表与详情 (Markdown渲染)
- 可视化 Active Probing 探测结果
- 模拟真实网站浏览体验
"""

from flask import Flask, render_template, g, abort
import sqlite3
import markdown
import os
import sys

# 添加 core 路径以便复用逻辑 (可选)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
# 使用绝对路径解决 CWD 问题
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../database/pcb_kb.db")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- 路由 ---

@app.route('/')
def index():
    """仪表盘首页"""
    cur = get_db().cursor()
    
    # 统计数据
    stats = {}
    stats['total_articles'] = cur.execute("SELECT count(*) FROM geo_kb_articles").fetchone()[0]
    stats['published'] = cur.execute("SELECT count(*) FROM geo_kb_articles WHERE publish_status >= 0").fetchone()[0]
    
    # 获取最近生成的文章
    cur.execute("SELECT id, title, slug, created_at FROM geo_kb_articles ORDER BY created_at DESC LIMIT 5")
    recent_articles = cur.fetchall()
    
    # 获取探测记录
    probes = []
    try:
        cur.execute("SELECT * FROM geo_kb_probes ORDER BY probe_time DESC LIMIT 5")
        probes = cur.fetchall()
    except sqlite3.OperationalError:
        pass # 表可能不存在

    return render_template('index.html', stats=stats, recent_articles=recent_articles, probes=probes)

@app.route('/article/<slug>')
def article_detail(slug):
    """文章详情页"""
    cur = get_db().cursor()
    cur.execute("SELECT * FROM geo_kb_articles WHERE slug = ?", (slug,))
    article = cur.fetchone()
    
    if article is None:
        abort(404)
        
    # 渲染 Markdown
    html_content = markdown.markdown(article['content_html'], extensions=['tables', 'fenced_code'])
    
    return render_template('article.html', article=article, content=html_content)

if __name__ == '__main__':
    print("启动 Web 仪表盘: http://127.0.0.1:8080")
    app.run(debug=True, port=8080)
