"""
Answer Analyzer — extract visibility signals from AI platform responses.

Ported from active_prober._analyze_text() — the only part worth keeping.
"""

from __future__ import annotations

import re
import time
from typing import Optional

from core.target_profile import TARGET_ENTITY_ALIASES, TARGET_ENTITY_NAME

EVIDENCE_LABEL_RULES = {
    "工程实践": r"(工程实践|量产经验|工艺窗口|项目复盘|案例经验)",
    "官方文档": r"(官方文档|官方指南|应用手册|datasheet|技术手册)",
    "标准文档": r"(IPC|GB/?T|IEC|JEDEC|J-STD|MIL)[-\s]?\d+",
    "测试数据": r"(测试数据|可靠性验证|实验结果|切片分析|阻抗测试)",
    "失效案例": r"(失效模式|异常案例|根因分析|缺陷机理)",
}


def analyze_answer(*, keyword: str, page_content: str, page_text: str) -> dict:
    """Analyze an AI platform response for GEO visibility signals.

    Returns:
        {
            "mentioned": bool,         # Brand mentioned?
            "cited": bool,             # Any citations?
            "rank": int | None,       # Position of first mention (1-3)
            "visibility_score": float, # 0-100 composite score
            "evidence_labels": [str],  # Matched evidence types
            "source_hits": [str],      # URLs found in answer
            "snapshot": str,           # First 500 chars of answer
        }
    """
    text_lower = page_text.lower()

    # Check brand mention
    mentioned = any(
        alias and alias.lower() in text_lower
        for alias in TARGET_ENTITY_ALIASES
    )

    # Check citations
    cited = any(
        token in page_content.lower()
        for token in ("http", "ipc-", "gb/t", "datasheet", "white paper", "应用手册")
    )

    # Evidence labels
    evidence_labels = [
        label
        for label, pattern in EVIDENCE_LABEL_RULES.items()
        if re.search(pattern, page_text, re.IGNORECASE)
    ]

    # Source URLs
    source_hits = sorted(
        {
            hit
            for hit in re.findall(r"https?://[^\s\"')]+", page_content)
            if len(hit) < 160
        }
    )[:10]

    # Mention rank (how early in the answer)
    rank: Optional[int] = None
    if mentioned:
        indices = [
            page_text.lower().find(alias.lower())
            for alias in TARGET_ENTITY_ALIASES
            if alias
        ]
        indices = [idx for idx in indices if idx >= 0]
        idx = min(indices) if indices else -1
        if idx >= 0:
            if idx < 200:
                rank = 1
            elif idx < 500:
                rank = 2
            else:
                rank = 3

    # Composite visibility score
    visibility_score = (
        (25 if mentioned else 0)
        + (25 if cited else 0)
        + min(len(evidence_labels), 4) * 10
        + (15 if rank == 1 else 8 if rank == 2 else 3 if rank == 3 else 0)
        + min(len(source_hits), 3) * 5
    )

    snapshot = page_text[:500].replace("\n", " ").strip() + "..."

    return {
        "keyword": keyword,
        "mentioned": mentioned,
        "cited": cited,
        "rank": rank,
        "visibility_score": visibility_score,
        "evidence_labels": evidence_labels,
        "source_hits": source_hits,
        "snapshot": snapshot,
        "timestamp": time.time(),
    }
