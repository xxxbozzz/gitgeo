"""
自动内链引擎 (Auto Linker)
===========================
文章通过质检后，自动扫描已发布文章并建立双向内链。

核心逻辑：
    1. 读取所有已发布文章的标题和关键词
    2. 在当前文章正文中匹配相关术语
    3. 将首次出现的术语替换为 Markdown 内链
    4. 在 geo_links 表记录链接关系
    5. 反向：在旧文章中也插入指向新文章的链接

使用方法：
    from core.linker import AutoLinker
    linker = AutoLinker()
    linker.link_article(article_id)
"""

import re
import logging
from core.db_manager import db_manager

log = logging.getLogger("GEO.Linker")


class AutoLinker:
    """知识库自动内链引擎"""

    # 不应被链接的短词（避免误匹配）
    MIN_KEYWORD_LEN = 3

    def __init__(self, base_url: str = "/wiki"):
        self.base_url = base_url

    def link_article(self, article_id: int) -> dict:
        """
        为指定文章建立内链。
        返回 {"outgoing": N, "incoming": M} 表示插入了多少条链接。
        """
        cnx = db_manager.get_connection()
        if not cnx:
            log.error("数据库连接失败，内链中止")
            return {"outgoing": 0, "incoming": 0}

        try:
            cursor = cnx.cursor(dictionary=True)

            # ── 读取当前文章 ──
            cursor.execute(
                "SELECT id, title, slug, content_markdown "
                "FROM geo_articles WHERE id = %s", (article_id,)
            )
            current = cursor.fetchone()
            if not current or not current["content_markdown"]:
                log.warning(f"文章 {article_id} 不存在或无内容")
                return {"outgoing": 0, "incoming": 0}

            # ── 读取所有其他已发布文章 ──
            cursor.execute(
                "SELECT id, title, slug, content_markdown "
                "FROM geo_articles WHERE id != %s AND publish_status >= 1",
                (article_id,),
            )
            others = cursor.fetchall()

            if not others:
                log.info("没有其他已发布文章，跳过内链")
                return {"outgoing": 0, "incoming": 0}

            outgoing = 0  # 当前文章 → 其他文章
            incoming = 0  # 其他文章 → 当前文章

            # ── 正向：在当前文章中插入指向其他文章的链接 ──
            new_content = current["content_markdown"]
            for other in others:
                anchor = self._extract_anchor(other["title"])
                if not anchor or len(anchor) < self.MIN_KEYWORD_LEN:
                    continue

                # 跳过已经存在的链接
                if self._link_exists(cursor, current["id"], other["id"]):
                    continue

                # 在正文中查找关键词（只替换首次出现，避免过度链接）
                if anchor in new_content:
                    link_url = f'{self.base_url}/{other["slug"]}' if other["slug"] else f'{self.base_url}/article/{other["id"]}'
                    link_md = f'[{anchor}]({link_url})'

                    # 只替换第一次出现，且不在标题行和已有链接中替换
                    new_content = self._safe_replace_first(new_content, anchor, link_md)
                    self._save_link(cursor, current["id"], other["id"], anchor)
                    outgoing += 1
                    log.info(f"  → 出链: {anchor} → 文章#{other['id']}")

            # 更新当前文章内容
            if outgoing > 0:
                cursor.execute(
                    "UPDATE geo_articles SET content_markdown = %s WHERE id = %s",
                    (new_content, current["id"]),
                )

            # ── 反向：在其他文章中插入指向当前文章的链接 ──
            current_anchor = self._extract_anchor(current["title"])
            if current_anchor and len(current_anchor) >= self.MIN_KEYWORD_LEN:
                current_url = f'{self.base_url}/{current["slug"]}' if current["slug"] else f'{self.base_url}/article/{current["id"]}'
                current_link = f'[{current_anchor}]({current_url})'

                for other in others:
                    if self._link_exists(cursor, other["id"], current["id"]):
                        continue

                    other_content = other["content_markdown"] or ""
                    if current_anchor in other_content:
                        updated = self._safe_replace_first(other_content, current_anchor, current_link)
                        cursor.execute(
                            "UPDATE geo_articles SET content_markdown = %s WHERE id = %s",
                            (updated, other["id"]),
                        )
                        self._save_link(cursor, other["id"], current["id"], current_anchor)
                        incoming += 1
                        log.info(f"  ← 入链: 文章#{other['id']} → {current_anchor}")

            cnx.commit()
            log.info(f"🔗 内链完成 [文章#{article_id}]: 出链 {outgoing}, 入链 {incoming}")
            return {"outgoing": outgoing, "incoming": incoming}

        except Exception as e:
            log.error(f"内链异常: {e}")
            cnx.rollback()
            return {"outgoing": 0, "incoming": 0}
        finally:
            cursor.close()
            cnx.close()

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    @staticmethod
    def _extract_anchor(title: str) -> str:
        """
        从标题中提取核心关键词作为锚文本。
        例如: "PCB飞针测试技术参数详解：IPC-9252B" → "PCB飞针测试"
        """
        if not title:
            return ""

        # 去掉副标题（冒号/破折号后的部分）
        core = re.split(r'[：:—\-|]', title)[0].strip()

        # 去掉常见修饰词
        for suffix in ["技术参数详解", "深度分析", "详解", "全解析", "可靠性验证",
                        "工艺技术", "设计与实现", "原理与应用", "深度解析"]:
            core = core.replace(suffix, "")

        return core.strip()

    @staticmethod
    def _safe_replace_first(content: str, keyword: str, replacement: str) -> str:
        """
        只替换正文中第一次出现的关键词。
        跳过标题行（#开头）和已有的 Markdown 链接中的文字。
        """
        lines = content.split("\n")
        replaced = False
        result = []

        for line in lines:
            if replaced or line.startswith("#") or f"[{keyword}]" in line:
                result.append(line)
                continue

            if keyword in line:
                # 确保不在已有链接 [...](...)  内部
                # 简单检查：keyword 前面不是 [ 字符
                idx = line.find(keyword)
                before = line[:idx]
                if "[" in before and "](" not in before[before.rfind("["):]:
                    result.append(line)
                    continue

                line = line.replace(keyword, replacement, 1)
                replaced = True

            result.append(line)

        return "\n".join(result)

    @staticmethod
    def _link_exists(cursor, source_id: int, target_id: int) -> bool:
        """检查链接是否已存在"""
        cursor.execute(
            "SELECT 1 FROM geo_links WHERE source_id=%s AND target_id=%s LIMIT 1",
            (source_id, target_id),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def _save_link(cursor, source_id: int, target_id: int, anchor: str, weight: float = 1.0):
        """写入链接关系"""
        cursor.execute(
            "INSERT INTO geo_links (source_id, target_id, anchor_text, weight) "
            "VALUES (%s, %s, %s, %s)",
            (source_id, target_id, anchor, weight),
        )
