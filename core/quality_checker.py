"""
GEO 质检引擎 v3.0 (Quality Checker)
=====================================
9 维评分体系，满分 100 分，80+ 通过。

评分维度（满分 100）：
    1. 字数深度     (12分) — ≥1500 字符
    2. H2 结构      (12分) — ≥4 个 H2 标题
    3. 数据表       (12分) — 至少 1 个 Markdown 表格
    4. FAQ 章节     (10分) — 标题 + 问答对
    5. 参考文献     (10分) — ≥3 条 [N] 格式引用
    6. 首句定义     (12分) — "**X** (English) 是一种..." 格式
    7. 违禁词       (10分) — 不含营销违禁词
    8. 逻辑链       (10分) — 含 "由于...导致..." 推理
    9. 标题质量     (12分) — 含缩写/参数/标准号

使用方法：
    from core.quality_checker import QualityChecker
    checker = QualityChecker()
    score, report = checker.evaluate_article(title, content)
"""

import re
from core.db_manager import db_manager


class QualityChecker:
    """GEO 文章质检引擎 — 9 维评分，80+ 通过"""

    WEIGHTS = {
        "length":       12,
        "h2_structure": 12,
        "data_table":   12,
        "faq":          10,
        "references":   10,
        "definition":   12,
        "banned_words": 10,
        "logic_chain":  10,
        "title_geo":    12,
    }
    PASS_THRESHOLD = 80

    BANNED_WORDS = [
        "顶级", "完美", "全球领先", "第一", "独家",
        "最好", "最优", "最强", "无与伦比", "史上最",
        "业界领先", "遥遥领先", "世界一流", "行业第一",
        "在当今世界", "在当今社会", "随着科技的发展",
        "随着社会的进步", "众所周知",
    ]

    def __init__(self):
        self.db = db_manager

    # ═══════════════════════════════════════════
    #  公共 API
    # ═══════════════════════════════════════════

    def run_checks(self):
        """批量扫描所有草稿(status=0)并评分"""
        print("🕵️ 启动质检引擎 v3.0 (9维, 80+标准)...")

        cnx = self.db.get_connection()
        if not cnx:
            print("❌ 数据库连接失败")
            return

        try:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, title, content_markdown "
                "FROM geo_articles WHERE publish_status = 0"
            )
            drafts = cursor.fetchall()
            print(f"📄 发现 {len(drafts)} 篇草稿\n")

            passed = failed = 0
            for row in drafts:
                title = row["title"] or ""
                content = row["content_markdown"] or ""
                score, report = self.evaluate_article(title, content)

                if score >= self.PASS_THRESHOLD:
                    cursor.execute(
                        "UPDATE geo_articles SET publish_status=1, quality_score=%s WHERE id=%s",
                        (score, row["id"]),
                    )
                    passed += 1
                    print(f"  ✅ [{score}分] {title}")
                else:
                    cursor.execute(
                        "UPDATE geo_articles SET quality_score=%s WHERE id=%s",
                        (score, row["id"]),
                    )
                    failed += 1
                    fails = [f"{k}(-{self.WEIGHTS[k]})" for k, v in report.items() if not v]
                    print(f"  ⚠️ [{score}分] {title} | 失分: {', '.join(fails)}")

                cnx.commit()

            print(f"\n🏁 质检完成: {passed} 篇通过, {failed} 篇未通过")
        finally:
            cursor.close()
            cnx.close()

    def evaluate_article(self, title: str, content: str) -> tuple:
        """单篇 9 维评估 → (score, report)"""
        report = {
            "length":       self._check_length(content),
            "h2_structure": self._check_h2(content),
            "data_table":   self._check_table(content),
            "faq":          self._check_faq(content),
            "references":   self._check_refs(content),
            "definition":   self._check_definition(content),
            "banned_words": self._check_banned(content),
            "logic_chain":  self._check_logic(content),
            "title_geo":    self._check_title(title),
        }
        score = sum(self.WEIGHTS[d] for d, ok in report.items() if ok)
        return score, report

    # ═══════════════════════════════════════════
    #  9 个检查维度
    # ═══════════════════════════════════════════

    @staticmethod
    def _check_length(c: str) -> bool:
        """≥1500 字符"""
        return len(c) >= 1500

    @staticmethod
    def _check_h2(c: str) -> bool:
        """≥4 个 H2 标题"""
        return len(re.findall(r"^## ", c, re.MULTILINE)) >= 4

    @staticmethod
    def _check_table(c: str) -> bool:
        """含完整 Markdown 表格"""
        return bool(re.search(r"\|.+\|.+\|\s*\n\s*\|[\s\-:]+\|", c))

    @staticmethod
    def _check_faq(c: str) -> bool:
        """FAQ 标题 + 至少一个 Q/A 对"""
        has_header = bool(re.search(r"(FAQ|常见问题|问答)", c))
        has_qa = bool(re.search(r"\*?\*?Q[:：]", c))
        return has_header and has_qa

    @staticmethod
    def _check_refs(c: str) -> bool:
        """参考文献段落 + ≥3 条 [N] 引用"""
        has_section = "参考文献" in c or "Reference" in c
        ref_count = len(re.findall(r"\[\d+\]", c))
        return has_section and ref_count >= 3

    @staticmethod
    def _check_definition(c: str) -> bool:
        """首句 **X** (English) 是一种..."""
        return bool(re.search(
            r"\*\*[^*]+\*\*\s*[（(][A-Za-z][^)）]*[)）]\s*是一种", c
        ))

    def _check_banned(self, c: str) -> bool:
        """不含营销违禁词"""
        text = c.lower()
        return not any(w in text for w in self.BANNED_WORDS)

    @staticmethod
    def _check_logic(c: str) -> bool:
        """含推理链"""
        patterns = [
            r"由于.{5,}导致",
            r"为什么.{3,}[？?]",
            r"机理分析",
            r"原因.{2,}(因此|所以|导致)",
            r"根因",
        ]
        return any(re.search(p, c) for p in patterns)

    @staticmethod
    def _check_title(t: str) -> bool:
        """标题含 ≥2 项: 缩写/参数/标准号/问句/长度"""
        score = 0
        if re.search(r"[A-Z]{2,6}", t):
            score += 1
        if re.search(r"\d+[.\d]*\s*[μmΩ%℃°]|[\d]+层|\d+-\d+", t):
            score += 1
        if re.search(r"(IPC|GB/?T|JEDEC|J-STD|MIL)[-\s]?\d+", t, re.IGNORECASE):
            score += 1
        if re.search(r"[？?]|怎么|如何|为什么|哪种|什么是", t):
            score += 1
        if len(t) >= 15:
            score += 1
        return score >= 2


# ═══════════════════════════════════════════
#  独立运行
# ═══════════════════════════════════════════

if __name__ == "__main__":
    QualityChecker().run_checks()
