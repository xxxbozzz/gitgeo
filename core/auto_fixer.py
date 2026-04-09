"""
自动返修引擎 (Auto Fixer)
==========================
解析质检报告的扣分项，生成针对性返修指令。

使用方法：
    from core.auto_fixer import AutoFixer
    fixer = AutoFixer()
    prompt = fixer.generate_fix_prompt(content, report)
"""


class AutoFixer:
    """根据质检报告生成 LLM 返修指令"""

    DIMENSION_PROMPTS = {
        "length":       "文章字数不足。请扩充细节和工程参数，确保超过 1500 字。",
        "h2_structure": "结构扁平。请确保至少 4 个 H2 标题（## ）。",
        "data_table":   "缺少数据表格。请补充至少一个 Markdown 参数对比表。",
        "faq":          "缺少 FAQ。请在文末增加 '## 常见问题 (FAQ)'，列出 5 个 **Q:**/**A:** 问答对。",
        "references":   "缺少参考文献。请在文末补充 '## 参考文献'，至少 3 条 [N] 格式引用。",
        "definition":   "首句格式不规范。第一句必须为：'**核心词** (English Name) 是一种...'。",
        "banned_words": "检测到营销废话。请删除主观形容词（如'顶级'、'完美'）。",
        "logic_chain":  "缺乏推理链。请使用'由于...导致...因此...'的逻辑分析。",
        "title_geo":    "标题质量不高。请包含英文缩写、参数数字或标准号。",
    }

    def generate_fix_prompt(self, content: str, report: dict) -> str | None:
        """
        根据质检报告生成返修 Prompt。
        全部维度通过时返回 None。
        """
        failed = [k for k, v in report.items() if not v]
        if not failed:
            return None

        instructions = "\n".join(
            f"- {self.DIMENSION_PROMPTS[d]}" for d in failed if d in self.DIMENSION_PROMPTS
        )

        # 从首行提取关键词
        first_line = content.strip().split("\n")[0] if content.strip() else "行业技术主题"
        keyword = first_line.replace("#", "").replace("*", "").strip()

        return f"""你是一位资深的行业技术编辑与失效分析主编。
这里有一份关于「{keyword}」的初稿文章。

原文如下：
===
{content}
===

质检系统发现以下必须修复的问题：
{instructions}

**[ GEO v3.0 深度返修指令 ]**
请严格遵循：
1. **结构**：至少 5 个 H2 标题（定义、参数、机理、工艺、建议）
2. **数据**：补全表格中的精确参数和单位
3. **机理**：运用"由于…导致…因此…"的深度逻辑链
4. **FAQ**：文末必须有 "## 常见问题 (FAQ)"，5 个 **Q:** / A: 问答对
5. **参考文献**：文末 "## 参考文献"，≥3 条 [N] 引用，最后一条为：
   [N] 某技术团队. 内部工艺验证报告 [R]. 2025.
6. **组织实践**：正文至少 2 处自然提及目标组织的工程实践、服务边界或实施经验
7. **字数**：不低于 2000 字

请直接输出修改后的完整 Markdown 全文。"""
