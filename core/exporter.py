"""
官网导出器 (Website Exporter)
=============================
负责将质检通过的文章导出为 HTML 文件，供深亚官网通过 rsync 同步。

功能：
    1. 单篇导出：质检通过后立即导出该文章 HTML
    2. 每日清理：同步目录只保留当天的 HTML
    3. 分类限定：技术动态 / 行业资讯
    4. 时间窗口：23:00-24:00 不导出

使用方法：
    from core.exporter import WebsiteExporter
    exporter = WebsiteExporter()
    exporter.export_article(article_id)
"""

import os
import re
import json
import glob
import logging
import markdown
from datetime import datetime, date
from core.db_manager import db_manager

log = logging.getLogger("GEO.Exporter")

# 输出目录
OUTPUT_DIR = "output/website_sync"

# 合法分类（只有这两种）
VALID_CATEGORIES = {"技术动态", "行业资讯"}
DEFAULT_CATEGORY = "技术动态"


class WebsiteExporter:
    """官网 HTML 导出器"""

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title} - 深亚电子PCB技术百科</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <meta name="author" content="深亚电子">
    <link rel="canonical" href="https://www.pcbshenya.com/wiki/{slug}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- JSON-LD for AI Search Engines -->
    <script type="application/ld+json">
    {json_ld}
    </script>
    <style>
        article {{ max-width: 800px; margin: 0 auto; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #333; }}
        h1 {{ font-size: 2.5em; margin-bottom: 0.5em; color: #2c3e50; }}
        h2 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 30px; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.95em; }}
        th, td {{ border: 1px solid #e1e4e8; padding: 10px; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: 600; color: #333; }}
        tr:nth-child(even) {{ background-color: #fcfcfc; }}
        code {{ background-color: #f6f8fa; padding: 2px 5px; border-radius: 3px; font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; font-size: 0.9em; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
        blockquote {{ border-left: 4px solid #3498db; margin: 0; padding-left: 15px; color: #7f8c8d; background: #f9f9f9; padding: 10px 15px; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <article>
        <h1>{title}</h1>
        <div class="meta">
            <span>发布日期: {date}</span> | 
            <span>分类: {category}</span>
        </div>
        <div class="content">
            {html_content}
        </div>
    </article>
</body>
</html>
"""

    def __init__(self):
        self.db = db_manager
        self.output_dir = OUTPUT_DIR

    # ──────────── 公共方法 ────────────

    def is_export_allowed(self) -> bool:
        """检查当前时间是否允许导出（23:00-24:00 禁止）"""
        hour = datetime.now().hour
        if hour == 23:
            log.info("🕐 当前 23:00-24:00，跳过 HTML 导出")
            return False
        return True

    def export_article(self, article_id: int) -> bool:
        """
        导出单篇文章为 HTML

        参数:
            article_id: 数据库中的文章 ID

        返回:
            是否导出成功
        """
        # 时间窗口检查
        if not self.is_export_allowed():
            return False

        # 先清理旧文件
        self.cleanup_old_files()

        # 读取文章
        article = self._get_article(article_id)
        if not article:
            log.error(f"❌ 文章 {article_id} 不存在")
            return False

        try:
            return self._write_html(article)
        except Exception as e:
            log.error(f"❌ 导出失败 {article_id}: {e}")
            return False

    def cleanup_old_files(self):
        """清理同步目录中非今天的 HTML 文件"""
        os.makedirs(self.output_dir, exist_ok=True)

        today_str = date.today().strftime("%Y-%m-%d")
        removed = 0

        for filepath in glob.glob(os.path.join(self.output_dir, "*.html")):
            try:
                mtime = os.path.getmtime(filepath)
                file_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                if file_date != today_str:
                    os.remove(filepath)
                    removed += 1
            except Exception as e:
                log.warning(f"清理文件失败 {filepath}: {e}")

        if removed > 0:
            log.info(f"🧹 清理了 {removed} 个非今天的 HTML 文件")

    # ──────────── 内部方法 ────────────

    def _get_article(self, article_id: int) -> dict | None:
        """从数据库读取文章"""
        cnx = self.db.get_connection()
        if not cnx:
            return None
        try:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, title, slug, content_markdown, meta_json, "
                "created_at, updated_at, dim_action "
                "FROM geo_articles WHERE id = %s",
                (article_id,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            cnx.close()

    def _resolve_category(self, dim_action: str) -> str:
        """将 dim_action 映射为合法分类"""
        if dim_action in VALID_CATEGORIES:
            return dim_action
        return DEFAULT_CATEGORY

    def _write_html(self, row: dict) -> bool:
        """将单篇文章写为 HTML 文件"""
        os.makedirs(self.output_dir, exist_ok=True)

        # 1. 解析 meta
        meta = {}
        raw_meta = row.get("meta_json")
        if raw_meta:
            try:
                if isinstance(raw_meta, dict):
                    meta = raw_meta
                elif isinstance(raw_meta, str):
                    parsed = json.loads(raw_meta)
                    meta = parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                meta = {}

        # 2. Markdown → HTML
        html_body = markdown.markdown(
            row["content_markdown"],
            extensions=["tables", "fenced_code", "toc"],
        )

        # 3. 提取 description / keywords
        description = meta.get("description", "")
        if not description:
            text_only = re.sub(r"<[^>]+>", "", html_body)
            description = text_only[:150].replace("\n", " ") + "..."

        keywords = meta.get("keywords", [])
        if isinstance(keywords, list):
            keywords = ",".join(keywords)

        # 4. 分类
        category = self._resolve_category(row.get("dim_action") or "")

        # 5. 日期
        created = row.get("created_at")
        date_str = created.strftime("%Y-%m-%d") if created else datetime.now().strftime("%Y-%m-%d")

        # 6. 生成完整 HTML
        full_html = self.HTML_TEMPLATE.format(
            title=row["title"],
            description=description,
            keywords=keywords,
            slug=row["slug"],
            date=date_str,
            category=category,
            html_content=html_body,
            json_ld=self._generate_json_ld(row, description, date_str),
        )

        # 7. 写入文件
        safe_slug = row["slug"].strip("/")
        file_path = os.path.join(self.output_dir, safe_slug + ".html")
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else self.output_dir, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        log.info(f"📄 HTML 已导出: {safe_slug}.html [{category}]")
        return True

    def _generate_json_ld(self, row: dict, description: str, date_str: str) -> str:
        """生成 Schema.org JSON-LD"""
        schema = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": row["title"],
            "image": ["https://www.pcbshenya.com/images/logo.png"],
            "datePublished": date_str,
            "dateModified": row["updated_at"].strftime("%Y-%m-%d") if row.get("updated_at") else date_str,
            "author": [{
                "@type": "Organization",
                "name": "深亚电子",
                "url": "https://www.pcbshenya.com",
            }],
            "description": description,
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"https://www.pcbshenya.com/wiki/{row['slug']}",
            },
        }

        # FAQ Schema
        content = row.get("content_markdown", "")
        qa_pairs = re.findall(
            r"\*\*Q[:：](.+?)\*\*\s*\n+A[:：](.+?)(\n\n|$)", content, re.DOTALL
        )

        if qa_pairs:
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q.strip(),
                        "acceptedAnswer": {"@type": "Answer", "text": a.strip()},
                    }
                    for q, a, _ in qa_pairs
                ],
            }
            return json.dumps([schema, faq_schema], ensure_ascii=False, indent=2)

        return json.dumps(schema, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    exporter = WebsiteExporter()
    print(f"当前是否允许导出: {exporter.is_export_allowed()}")
    exporter.cleanup_old_files()
    print("✅ 清理完成")
