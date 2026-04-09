"""
自动内链管理器 (Link Manager)
==============================
本模块负责构建文章之间的内部链接图谱。

工作流程：
    1. 从 geo_keywords + geo_articles 构建 "关键词 → 文章" 映射表
    2. 扫描待发布文章的正文
    3. 发现关键词匹配时，在首次出现处插入 Markdown 链接
    4. 将链接关系写入 geo_links 图谱表

约束规则：
    - 每个关键词只链接首次出现
    - 每篇文章最多插入 10 个内链
    - 已经被 Markdown 链接包裹的关键词跳过
"""

import re
from core.db_manager import db_manager


class LinkManager:
    """文章内链引擎 — 基于关键词匹配的自动内链构建"""

    MAX_LINKS_PER_ARTICLE = 10  # 单篇文章最大内链数

    def __init__(self):
        self.db = db_manager

    def build_keyword_map(self) -> dict:
        """
        构建关键词到文章的映射表

        返回:
            {keyword: {'slug': slug, 'id': article_id}}
        """
        cnx = self.db.get_connection()
        if not cnx:
            return {}

        cursor = cnx.cursor(dictionary=True)
        query = """
            SELECT k.keyword, a.slug, a.id AS article_id
            FROM geo_keywords k
            JOIN geo_articles a ON k.target_article_id = a.id
            WHERE a.publish_status > 0
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        cnx.close()

        return {
            row['keyword']: {'slug': row['slug'], 'id': row['article_id']}
            for row in results
        }

    def process_article(self, article_id: int, content: str) -> tuple:
        """
        扫描文章内容，在关键词首次出现处插入内链

        参数:
            article_id: 源文章 ID
            content: 文章正文 (Markdown)

        返回:
            (updated_content, links_added) — 更新后的正文 + 新增的链接列表
        """
        keyword_map = self.build_keyword_map()
        # 按关键词长度降序排列，优先匹配长关键词（如 "PCB 阻抗控制" 优先于 "PCB"）
        sorted_keywords = sorted(keyword_map.keys(), key=len, reverse=True)

        links_added = []
        new_content = content
        link_count = 0

        for kw in sorted_keywords:
            if link_count >= self.MAX_LINKS_PER_ARTICLE:
                break

            # 跳过已被链接的关键词
            if f"[{kw}](" in new_content:
                continue

            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            if not pattern.search(new_content):
                continue

            target = keyword_map[kw]
            link_md = f"[{kw}](/wiki/{target['slug']})"

            # 替换首次出现
            new_content, count = pattern.subn(link_md, new_content, count=1)
            if count > 0:
                links_added.append({
                    'source_id': article_id,
                    'target_id': target['id'],
                    'anchor': kw,
                })
                link_count += 1

        return new_content, links_added

    def run_auto_linking(self):
        """对所有 Pending 状态文章执行自动内链"""
        print("🔗 启动自动内链服务...")

        cnx = self.db.get_connection()
        if not cnx:
            return

        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT id, content_markdown FROM geo_articles WHERE publish_status = 1")
        articles = cursor.fetchall()
        total_links = 0

        for row in articles:
            updated_content, links = self.process_article(row['id'], row['content_markdown'])

            if links:
                # 更新文章正文
                cursor.execute(
                    "UPDATE geo_articles SET content_markdown = %s WHERE id = %s",
                    (updated_content, row['id']),
                )
                # 写入链接图谱
                for link in links:
                    cursor.execute(
                        "INSERT IGNORE INTO geo_links (source_id, target_id, anchor_text, weight) VALUES (%s, %s, %s, 1)",
                        (link['source_id'], link['target_id'], link['anchor']),
                    )
                cnx.commit()
                total_links += len(links)
                print(f"  ✅ 文章 {row['id']}: 插入 {len(links)} 条内链")

        cursor.close()
        cnx.close()
        print(f"🏁 自动内链完成，共新增 {total_links} 条链接关系")


if __name__ == "__main__":
    linker = LinkManager()
    linker.run_auto_linking()
