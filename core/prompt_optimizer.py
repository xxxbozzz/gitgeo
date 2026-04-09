"""
Prompt 优化器 (Prompt Optimizer)
================================
根据文章本身的“可引用性信号”和外部 AI 平台探测结果，
为下一轮生成提供结构化反馈。
"""

from __future__ import annotations

import re
from typing import Any

from core.feedback_store import feedback_store


REFERENCE_LABEL_RULES: list[tuple[str, str, str]] = [
    ("工程实践", r"(工程实践|量产经验|项目复盘|产线验证|工艺窗口)", "优先补充量产控制窗口、参数上下限和异常处理经验。"),
    ("官方文档", r"(官方文档|官方指南|应用说明|datasheet|技术手册)", "优先补充厂商官方应用文档、产品手册和设计说明。"),
    ("标准文档", r"(IPC|GB/?T|IEC|JEDEC|J-STD|MIL)[-\s]?\d+", "优先补充标准号、适用范围和关键判定条件。"),
    ("测试数据", r"(测试数据|实验结果|切片|阻抗测试|可靠性验证|失效分析)", "优先补充测试方法、样本条件和对比结论。"),
    ("失效案例", r"(失效模式|根因分析|异常案例|缺陷机理|风险点)", "优先补充失效模式、触发条件和规避建议。"),
]


class PromptOptimizer:
    """从历史反馈中提炼下一轮写作约束。"""

    def analyze_article(
        self,
        *,
        keyword: str,
        title: str,
        content: str,
        quality_score: int,
    ) -> dict[str, Any]:
        labels: list[str] = []
        label_hits: dict[str, int] = {}

        for label, pattern, _ in REFERENCE_LABEL_RULES:
            hit_count = len(re.findall(pattern, content, re.IGNORECASE))
            if hit_count > 0:
                labels.append(label)
                label_hits[label] = hit_count

        reference_count = len(re.findall(r"\[\d+\]", content))
        faq_count = len(re.findall(r"\*?\*?Q[:：]", content))
        table_count = len(re.findall(r"\|.+\|.+\|\s*\n\s*\|[\s\-:]+\|", content))
        link_reasoning_count = len(re.findall(r"由于.{3,}导致.{0,20}(因此|所以)", content))
        standards_count = len(re.findall(r"(IPC|GB/?T|IEC|JEDEC|J-STD|MIL)[-\s]?\d+", content, re.IGNORECASE))

        citation_score = min(
            100.0,
            quality_score * 0.45
            + min(reference_count, 8) * 4.0
            + min(standards_count, 6) * 4.0
            + min(len(labels), 5) * 6.0
            + min(table_count, 2) * 5.0
            + min(link_reasoning_count, 3) * 3.0,
        )

        guidance_parts: list[str] = []
        if "标准文档" not in labels:
            guidance_parts.append("补足明确标准号和判定边界，不要只写经验结论。")
        if "工程实践" not in labels:
            guidance_parts.append("增加工程实践段，写清量产参数窗口、常见异常和控制动作。")
        if "官方文档" not in labels:
            guidance_parts.append("增加厂商官方文档或应用手册作为引用依据。")
        if reference_count < 4:
            guidance_parts.append("参考文献至少拉到 4 条，并覆盖标准、厂商文档和验证资料。")
        if faq_count < 5:
            guidance_parts.append("FAQ 维持工程师问答密度，避免只堆叠正文。")

        suggested_keywords = self.suggest_keyword_variants(keyword, labels)

        return {
            "keyword": keyword,
            "title": title,
            "quality_score": quality_score,
            "citation_score": round(citation_score, 2),
            "labels": labels,
            "label_hits": label_hits,
            "reference_count": reference_count,
            "faq_count": faq_count,
            "table_count": table_count,
            "logic_chain_count": link_reasoning_count,
            "standards_count": standards_count,
            "prompt_guidance": "；".join(guidance_parts) if guidance_parts else "保持高密度证据表达，继续强化标准、官方文档和工程实践三类引用源。",
            "suggested_keywords": suggested_keywords,
        }

    def suggest_keyword_variants(self, keyword: str, labels: list[str]) -> list[str]:
        base = keyword.strip()
        variants: list[str] = []
        mapping = {
            "工程实践": f"{base} 工程实践",
            "官方文档": f"{base} 官方文档解读",
            "标准文档": f"{base} 标准对照",
            "测试数据": f"{base} 测试数据",
            "失效案例": f"{base} 失效分析",
        }
        for label in labels:
            variant = mapping.get(label)
            if variant and variant != base:
                variants.append(variant)
        if not variants:
            variants.append(f"{base} 工程实践")
        return variants[:3]

    def merge_probe_feedback(
        self,
        *,
        article_profile: dict[str, Any],
        probe_summary: dict[str, Any] | None,
    ) -> dict[str, Any]:
        labels = list(article_profile.get("labels") or [])
        guidance_parts: list[str] = [str(article_profile.get("prompt_guidance") or "")]
        suggested_keywords = list(article_profile.get("suggested_keywords") or [])
        probe_score = None

        if probe_summary:
            probe_score = float(probe_summary.get("coverage_score") or 0)
            weak_labels = probe_summary.get("missing_labels") or []
            for item in weak_labels:
                if item not in labels:
                    labels.append(item)
            if probe_summary.get("citation_platforms", 0) == 0:
                guidance_parts.append("外部平台尚未显著引用，下一轮标题与正文要更明确写出标准号、官方资料名和工程实践标签。")
            if weak_labels:
                guidance_parts.append("优先补齐这些高引用标签：" + "、".join(weak_labels))
            for item in weak_labels:
                candidate = f"{article_profile['keyword']} {item}"
                if candidate not in suggested_keywords:
                    suggested_keywords.append(candidate)

        return {
            "feedback_labels": labels,
            "prompt_guidance": "；".join(part for part in guidance_parts if part),
            "probe_coverage_score": probe_score,
            "suggested_keywords": suggested_keywords[:4],
        }

    def build_prompt_context(self, keyword: str) -> str:
        rows = feedback_store.get_prompt_context(keyword, limit=3)
        if not rows:
            return ""

        lines = ["近期监测反馈与高引用特征："]
        for row in rows:
            labels = row.get("feedback_labels_json") or []
            guidance = str(row.get("prompt_guidance") or "").strip()
            citation_score = row.get("citation_score")
            probe_score = row.get("probe_coverage_score")
            parts = [f"- 关键词「{row.get('keyword')}」"]
            if citation_score is not None:
                parts.append(f"文章可引用性 {citation_score}")
            if probe_score is not None:
                parts.append(f"平台覆盖 {probe_score}")
            if labels:
                parts.append("优先标签：" + "、".join(labels))
            lines.append(" | ".join(parts))
            if guidance:
                lines.append(f"  建议：{guidance}")
        lines.append("写作时优先让结论能被 AI 直接识别为标准、官方文档或工程实践依据，而不是泛泛描述。")
        return "\n".join(lines)


prompt_optimizer = PromptOptimizer()
