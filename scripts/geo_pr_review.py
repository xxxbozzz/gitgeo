#!/usr/bin/env python3
"""
GitGeo GEO PR Review Bot
=========================
Automated GEO quality review on PR changes. Detects degradation across
6 dimensions and produces a structured block/pass report.

Dimensions:
  1. 9-dim quality score degradation
  2. FAQ / Reference / First-sentence-definition removal
  3. Capability store reference loss
  4. Prompt drift (becoming more generic)
  5. Multi-platform publishing config breakage
  6. AI visibility probe field integrity

Usage:
  python scripts/geo_pr_review.py                          # review current diff
  python scripts/geo_pr_review.py --base main --head feat  # review branch diff
  python scripts/geo_pr_review.py --json                   # JSON output for CI
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# ═══════════════════════════════════════════
#  File categories — which files affect which dimensions
# ═══════════════════════════════════════════

QUALITY_SCORE_FILES = {
    "core/quality_checker.py",
}

CONTENT_STRUCTURE_FILES = {
    "core/quality_checker.py",
    "core/tasks.py",
    "core/agents.py",
    "batch_generator.py",
    "core/auto_fixer.py",
}

CAPABILITY_STORE_FILES = {
    "core/capability_store.py",
    "knowledge-base/industry/shenya_pcb_capability_profile.json",
    "core/target_profile.py",
}

PROMPT_FILES = {
    "core/tasks.py",
    "core/agents.py",
    "core/prompt_optimizer.py",
    "batch_generator.py",
    "暗涌生文提示词模版",
    "core/trend_scout.py",
}

PUBLISH_CONFIG_FILES = {
    "core/publisher_adapters.py",
    "core/publish/adapters/zhihu.py",
    "core/publish/adapters/wechat_mp.py",
    "core/publish/adapters/dryrun.py",
    "core/publish/base.py",
    "core/publish/engine.py",
    "auto_publish.py",
    "backend/app/services/publications_service.py",
}

PROBE_FILES = {
    "core/active_prober.py",
    "core/target_profile.py",
    "core/prompt_optimizer.py",
}

KNOWLEDGE_BASE_DIR = "knowledge-base"

ALL_TRACKED_DIRS = {
    "core/",
    "backend/",
    "knowledge-base/",
    "batch_generator.py",
    "auto_publish.py",
    "暗涌生文提示词模版",
    ".github/workflows/",
}

# ═══════════════════════════════════════════
#  Quality baselines (snapshotted from current code)
# ═══════════════════════════════════════════

# quality_checker.py
QUALITY_PASS_THRESHOLD = 80
QUALITY_WEIGHTS: dict[str, int] = {
    "length": 12, "h2_structure": 12, "data_table": 12,
    "faq": 10, "references": 10, "definition": 12,
    "banned_words": 10, "logic_chain": 10, "title_geo": 12,
}
QUALITY_MIN_BANNED_WORDS = 19

# active_prober.py
PROBE_EVIDENCE_LABEL_KEYS = ["工程实践", "官方文档", "标准文档", "测试数据", "失效案例"]
PROBE_MIN_PLATFORM_COUNT = 4
PROBE_REQUIRED_RETURN_FIELDS = [
    "mentioned", "cited", "rank", "visibility_score",
    "evidence_labels", "source_hits",
]

# publisher_adapters.py
PUBLISH_REQUIRED_ADAPTERS = ["zhihu", "wechat", "dryrun"]

# capability store
CAPABILITY_MIN_SPEC_COUNT = 12
CAPABILITY_MIN_SOURCE_COUNT = 11
CAPABILITY_REQUIRED_SPEC_GROUPS = [
    "high_layer", "precision", "hdi", "plating",
    "impedance", "material", "backdrill", "rf_mmwave",
    "thermal", "surface_finish", "reliability",
]

# prompt structure
PROMPT_REQUIRED_H2_SECTIONS = ["定义", "场景", "参数", "实施", "风险", "FAQ"]
PROMPT_MIN_REF_COUNT = 3
PROMPT_MIN_FAQ_COUNT = 5
PROMPT_MIN_TABLE_COUNT = 1
PROMPT_MIN_LOGIC_COUNT = 2
PROMPT_MIN_WORD_COUNT = 2000


# ═══════════════════════════════════════════
#  Diff analysis helpers
# ═══════════════════════════════════════════

def get_changed_files(base: str = "HEAD~1", head: str = "HEAD") -> list[str]:
    """Get list of changed files between two refs."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT,
        )
        return [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except Exception as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        return []


def get_file_diff(filepath: str, base: str = "HEAD~1", head: str = "HEAD") -> str:
    """Get the diff for a specific file."""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base}...{head}", "--", filepath],
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT,
        )
        return result.stdout
    except Exception:
        return ""


def get_file_content_at_ref(filepath: str, ref: str = "HEAD") -> str:
    """Get file content at a specific git ref."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{filepath}"],
            capture_output=True, text=True, timeout=15,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    # Fallback: read from disk
    try:
        return (PROJECT_ROOT / filepath).read_text(encoding="utf-8")
    except Exception:
        return ""


def count_diff_lines(diff: str, prefix: str) -> int:
    """Count added (+) or removed (-) lines in a diff."""
    return sum(1 for line in diff.split("\n") if line.startswith(prefix) and not line.startswith(prefix * 3))


# ═══════════════════════════════════════════
#  Dimension checkers
# ═══════════════════════════════════════════

class DimensionResult:
    """Result of a single dimension check."""
    def __init__(self, name: str, passed: bool, score: float, detail: str):
        self.name = name
        self.passed = passed
        self.score = score  # 0.0 - 1.0
        self.detail = detail
        self.blocking = not passed and score < 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.name,
            "passed": self.passed,
            "score": self.score,
            "blocking": self.blocking,
            "detail": self.detail,
        }


def check_quality_score_degradation(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Dimension 1: 9-dim quality score degradation.
    Checks if PASS_THRESHOLD was lowered, weights reduced, or banned words removed.
    """
    if not QUALITY_SCORE_FILES & set(files):
        return DimensionResult(
            "质量分体系", True, 1.0,
            "quality_checker.py 未变更，质量分体系无退化风险。"
        )

    diff = get_file_diff("core/quality_checker.py", base, head)
    current = get_file_content_at_ref("core/quality_checker.py", head)
    previous = get_file_content_at_ref("core/quality_checker.py", base)

    issues = []
    score = 1.0

    # Check PASS_THRESHOLD
    prev_threshold = re.search(r"PASS_THRESHOLD\s*=\s*(\d+)", previous)
    curr_threshold = re.search(r"PASS_THRESHOLD\s*=\s*(\d+)", current)
    if prev_threshold and curr_threshold:
        old_val = int(prev_threshold.group(1))
        new_val = int(curr_threshold.group(1))
        if new_val < old_val:
            issues.append(f"⚠️  PASS_THRESHOLD 从 {old_val} 降至 {new_val}（放宽了通过标准）")
            score -= 0.3

    # Check weight changes
    for dim_name in QUALITY_WEIGHTS:
        prev_w = re.search(rf"\"{dim_name}\":\s*(\d+)", previous)
        curr_w = re.search(rf"\"{dim_name}\":\s*(\d+)", current)
        if prev_w and curr_w:
            old_w = int(prev_w.group(1))
            new_w = int(curr_w.group(1))
            if new_w < old_w:
                issues.append(f"⚠️  {dim_name} 权重从 {old_w} 降至 {new_w}")
                score -= 0.1

    # Check banned words list
    prev_banned = re.findall(r"\"([^\"]+)\"", previous[previous.find("BANNED_WORDS"):previous.find("]", previous.find("BANNED_WORDS"))])
    curr_banned = re.findall(r"\"([^\"]+)\"", current[current.find("BANNED_WORDS"):current.find("]", current.find("BANNED_WORDS"))])
    removed_banned = set(prev_banned) - set(curr_banned)
    if removed_banned:
        issues.append(f"⚠️  违禁词列表删除了 {len(removed_banned)} 项：{', '.join(sorted(removed_banned)[:5])}")
        score -= 0.2

    score = max(0.0, score)
    if not issues:
        return DimensionResult("质量分体系", True, score, "质量评分体系无退化。")
    return DimensionResult(
        "质量分体系", score >= 0.5, score,
        "\n".join(issues)
    )


def check_content_structure(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Dimension 2: FAQ / References / First-sentence-definition integrity.
    Checks if structural requirements were removed from prompts or quality checks.
    """
    if not CONTENT_STRUCTURE_FILES & set(files):
        return DimensionResult(
            "内容结构完整性", True, 1.0,
            "内容结构相关文件未变更。"
        )

    issues = []
    score = 1.0

    # Check quality_checker.py for structural check removal
    if "core/quality_checker.py" in files:
        curr_qc = get_file_content_at_ref("core/quality_checker.py", head)
        checks_present = {
            "FAQ": bool(re.search(r"def _check_faq|_check_faq", curr_qc)),
            "参考文献": bool(re.search(r"def _check_refs|_check_refs", curr_qc)),
            "首句定义": bool(re.search(r"def _check_definition|_check_definition", curr_qc)),
        }
        for name, present in checks_present.items():
            if not present:
                issues.append(f"❌ quality_checker.py 中 {name} 检查函数被删除")
                score -= 0.3

    # Check prompt template for structural requirements
    prompt_files = [f for f in files if f in PROMPT_FILES]
    for pf in prompt_files:
        curr_content = get_file_content_at_ref(pf, head)
        prev_content = get_file_content_at_ref(pf, base)

        # Count H2 sections required
        prev_h2 = len(re.findall(r"##\s+", prev_content))
        curr_h2 = len(re.findall(r"##\s+", curr_content))

        # Count FAQ references
        prev_faq = prev_content.lower().count("faq") + prev_content.count("常见问题")
        curr_faq = curr_content.lower().count("faq") + curr_content.count("常见问题")

        # Count reference format mentions
        prev_ref = prev_content.count("[1]") + prev_content.count("[N]")
        curr_ref = curr_content.count("[1]") + curr_content.count("[N]")

        # Count definition pattern mentions
        prev_def = prev_content.count("是一种") + prev_content.count("首句")
        curr_def = curr_content.count("是一种") + curr_content.count("首句")

        if curr_h2 < prev_h2 * 0.7:
            issues.append(f"⚠️  {pf} 中 H2 段落要求减少（{prev_h2} → {curr_h2}）")
            score -= 0.15
        if curr_faq < prev_faq * 0.7:
            issues.append(f"⚠️  {pf} 中 FAQ 要求减少")
            score -= 0.15
        if curr_ref < prev_ref * 0.7:
            issues.append(f"⚠️  {pf} 中参考文献要求减少")
            score -= 0.15
        if curr_def < prev_def * 0.7:
            issues.append(f"⚠️  {pf} 中首句定义要求减少")
            score -= 0.15

    score = max(0.0, score)
    if not issues:
        return DimensionResult("内容结构完整性", True, score, "FAQ/引用/首句定义结构完整。")
    return DimensionResult(
        "内容结构完整性", score >= 0.4, score,
        "\n".join(issues)
    )


def check_capability_references(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Dimension 3: Capability store reference integrity.
    Checks if capability specs, sources, or build_context functions are broken.
    """
    if not CAPABILITY_STORE_FILES & set(files):
        return DimensionResult(
            "能力库引用", True, 1.0,
            "能力库相关文件未变更。"
        )

    issues = []
    score = 1.0

    # Check capability profile JSON
    if "knowledge-base/industry/shenya_pcb_capability_profile.json" in files:
        curr_profile = get_file_content_at_ref(
            "knowledge-base/industry/shenya_pcb_capability_profile.json", head
        )
        prev_profile = get_file_content_at_ref(
            "knowledge-base/industry/shenya_pcb_capability_profile.json", base
        )
        try:
            curr_json = json.loads(curr_profile)
            prev_json = json.loads(prev_profile)
        except json.JSONDecodeError:
            return DimensionResult(
                "能力库引用", False, 0.0,
                "❌ shenya_pcb_capability_profile.json 格式损坏，无法解析。"
            )

        # Check spec count
        prev_specs = len(prev_json.get("specs", []))
        curr_specs = len(curr_json.get("specs", []))
        if curr_specs < prev_specs:
            removed = prev_specs - curr_specs
            issues.append(f"❌ 能力条目从 {prev_specs} 减少到 {curr_specs}（删除了 {removed} 项）")
            score -= 0.4

        # Check source count
        prev_sources = len(prev_json.get("sources", []))
        curr_sources = len(curr_json.get("sources", []))
        if curr_sources < prev_sources:
            removed = prev_sources - curr_sources
            issues.append(f"❌ 证据来源从 {prev_sources} 减少到 {curr_sources}（删除了 {removed} 项）")
            score -= 0.4

        # Check for missing evidence_refs
        curr_specs_list = curr_json.get("specs", [])
        curr_sources_codes = {s.get("source_code") for s in curr_json.get("sources", [])}
        for spec in curr_specs_list:
            for ref in spec.get("evidence_refs", []):
                if ref not in curr_sources_codes:
                    issues.append(f"⚠️  能力项「{spec.get('capability_name')}」引用了不存在的来源: {ref}")
                    score -= 0.1

        # Check required spec groups
        curr_groups = {s.get("group_code") for s in curr_specs_list}
        missing_groups = set(CAPABILITY_REQUIRED_SPEC_GROUPS) - curr_groups
        if missing_groups:
            issues.append(f"⚠️  能力分组缺失: {', '.join(sorted(missing_groups))}")
            score -= 0.3

    # Check capability_store.py core functions
    if "core/capability_store.py" in files:
        curr_cs = get_file_content_at_ref("core/capability_store.py", head)
        required_funcs = ["search_capabilities", "build_context", "save_capability_payload"]
        for func in required_funcs:
            if f"def {func}" not in curr_cs:
                issues.append(f"❌ capability_store.py 中 {func}() 函数丢失")
                score -= 0.3

    # Check target_profile.py
    if "core/target_profile.py" in files:
        curr_tp = get_file_content_at_ref("core/target_profile.py", head)
        if "TARGET_ENTITY_NAME" not in curr_tp or "TARGET_ENTITY_ALIASES" not in curr_tp:
            issues.append("❌ target_profile.py 中实体配置丢失")
            score -= 0.5

    score = max(0.0, score)
    if not issues:
        return DimensionResult("能力库引用", True, score, "能力库引用完整。")
    return DimensionResult(
        "能力库引用", score >= 0.5, score,
        "\n".join(issues)
    )


def check_prompt_drift(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Dimension 4: Prompt drift — is the prompt becoming more generic?
    Checks for: removal of specific rules, weakening of evidence requirements,
    loss of Chinese-first constraint, reduction of structural requirements.
    """
    if not PROMPT_FILES & set(files):
        return DimensionResult(
            "Prompt 特异性", True, 1.0,
            "Prompt 相关文件未变更。"
        )

    issues = []
    score = 1.0

    for pf in [f for f in files if f in PROMPT_FILES]:
        curr = get_file_content_at_ref(pf, head)
        prev = get_file_content_at_ref(pf, base)
        diff = get_file_diff(pf, base, head)

        if not diff:
            continue

        added_lines = count_diff_lines(diff, "+")
        removed_lines = count_diff_lines(diff, "-")

        # Check removal of specific evidence types
        evidence_keywords = ["工程实践", "官方文档", "标准文档", "测试数据", "失效案例"]
        for kw in evidence_keywords:
            prev_count = prev.count(kw)
            curr_count = curr.count(kw)
            if curr_count < prev_count:
                issues.append(f"⚠️  {pf} 中「{kw}」证据类型引用减少（{prev_count} → {curr_count}）")
                score -= 0.1

        # Check Chinese-first constraint
        chinese_markers = ["简体中文", "中文", "禁止输出英文"]
        for marker in chinese_markers:
            if marker in prev and marker not in curr:
                issues.append(f"⚠️  {pf} 中「{marker}」约束被移除")
                score -= 0.2

        # Check if removed lines exceed added lines significantly
        if removed_lines > added_lines * 2 and removed_lines > 5:
            issues.append(
                f"⚠️  {pf} 净删除 {removed_lines - added_lines} 行（+{added_lines}/-{removed_lines}），"
                "可能存在 Prompt 简化"
            )
            score -= 0.2

        # Check for specific rule numbers
        rule_pattern = re.findall(r"【规则\s*(\d+)】", prev)
        curr_rules = re.findall(r"【规则\s*(\d+)】", curr)
        if len(curr_rules) < len(rule_pattern):
            issues.append(f"⚠️  {pf} 中硬性规则从 {len(rule_pattern)} 条减少到 {len(curr_rules)} 条")
            score -= 0.25

    score = max(0.0, score)
    if not issues:
        return DimensionResult("Prompt 特异性", True, score, "Prompt 特异性未退化。")
    return DimensionResult(
        "Prompt 特异性", score >= 0.4, score,
        "\n".join(issues)
    )


def check_publish_config(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Dimension 5: Multi-platform publishing config integrity.
    Checks if platform adapters, ADAPTERS dict, or publishing workflows are broken.
    """
    if not PUBLISH_CONFIG_FILES & set(files):
        return DimensionResult(
            "多平台发布配置", True, 1.0,
            "发布配置相关文件未变更。"
        )

    issues = []
    score = 1.0

    # Check publisher_adapters.py
    if "core/publisher_adapters.py" in files:
        curr_adapter = get_file_content_at_ref("core/publisher_adapters.py", head)
        prev_adapter = get_file_content_at_ref("core/publisher_adapters.py", base)

        for adapter_name in PUBLISH_REQUIRED_ADAPTERS:
            # Check adapter registration exists in ADAPTERS dict
            adapter_key = f'"{adapter_name}"'
            if adapter_key not in curr_adapter:
                issues.append(f"❌ {adapter_name} 平台适配器注册丢失")
                score -= 0.3

        # Check ADAPTERS dict has all required keys
        for adapter_name in PUBLISH_REQUIRED_ADAPTERS:
            if f'"{adapter_name}"' not in curr_adapter:
                issues.append(f"❌ ADAPTERS 中缺少 {adapter_name} 平台")
                score -= 0.4

        # Check get_publisher_adapter function
        if "def get_publisher_adapter" not in curr_adapter:
            issues.append("❌ get_publisher_adapter() 函数丢失")
            score -= 0.3

    # Check platform-specific publishers exist
    for platform_file in ["core/publish/adapters/zhihu.py", "core/publish/adapters/wechat_mp.py"]:
        if platform_file in files:
            curr = get_file_content_at_ref(platform_file, head)
            if "def publish" not in curr:
                issues.append(f"❌ {platform_file} 中 publish() 方法丢失")
                score -= 0.3

    score = max(0.0, score)
    if not issues:
        return DimensionResult("多平台发布配置", True, score, "发布配置完整。")
    return DimensionResult(
        "多平台发布配置", score >= 0.5, score,
        "\n".join(issues)
    )


def check_probe_tracking(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Dimension 6: AI visibility probe field integrity.
    Checks if EVIDENCE_LABEL_RULES, PLATFORMS, _analyze_text tracking fields,
    and TARGET_ENTITY configs are intact.
    """
    if not PROBE_FILES & set(files):
        return DimensionResult(
            "AI 可见性探测", True, 1.0,
            "探测相关文件未变更。"
        )

    issues = []
    score = 1.0

    # Check active_prober.py
    if "core/active_prober.py" in files:
        curr_probe = get_file_content_at_ref("core/active_prober.py", head)
        prev_probe = get_file_content_at_ref("core/active_prober.py", base)

        # Check EVIDENCE_LABEL_RULES keys
        prev_labels = set(re.findall(r"\"([^\"]+)\":\s*r\"", prev_probe[prev_probe.find("EVIDENCE_LABEL_RULES"):prev_probe.find("}", prev_probe.find("EVIDENCE_LABEL_RULES"))]))
        curr_labels = set(re.findall(r"\"([^\"]+)\":\s*r\"", curr_probe[curr_probe.find("EVIDENCE_LABEL_RULES"):curr_probe.find("}", curr_probe.find("EVIDENCE_LABEL_RULES"))]))
        removed_labels = prev_labels - curr_labels
        if removed_labels:
            issues.append(f"⚠️  EVIDENCE_LABEL_RULES 删除标签: {', '.join(sorted(removed_labels))}")
            score -= 0.3

        # Check PLATFORMS count
        prev_platforms = len(re.findall(r"\"[a-z]+\":\s*\{", prev_probe[prev_probe.find("PLATFORMS"):prev_probe.find("}", prev_probe.find("PLATFORMS") + 500)]))
        curr_platforms = len(re.findall(r"\"[a-z]+\":\s*\{", curr_probe[curr_probe.find("PLATFORMS"):curr_probe.find("}", curr_probe.find("PLATFORMS") + 500)]))
        if curr_platforms < prev_platforms:
            issues.append(f"❌ 探测平台从 {prev_platforms} 个减少到 {curr_platforms} 个")
            score -= 0.4

        # Check _analyze_text method exists
        if "def _analyze_text" not in curr_probe:
            issues.append("❌ _analyze_text() 分析方法丢失")
            score -= 0.4

        # Check tracking fields in _analyze_text return dict
        if "def _analyze_text" in curr_probe:
            analyze_start = curr_probe.find("def _analyze_text")
            analyze_end = curr_probe.find("def ", analyze_start + 1)
            if analyze_end == -1:
                analyze_end = len(curr_probe)
            analyze_body = curr_probe[analyze_start:analyze_end]
            for field in PROBE_REQUIRED_RETURN_FIELDS:
                if f'"{field}"' not in analyze_body:
                    issues.append(f"⚠️  _analyze_text 返回值缺失字段: {field}")
                    score -= 0.15

        # Check probe() method exists
        if "def probe" not in curr_probe:
            issues.append("❌ probe() 探测方法丢失")
            score -= 0.3

        # Check summarize_results coverage_score
        if "coverage_score" not in curr_probe:
            issues.append("⚠️  summarize_results 中 coverage_score 字段丢失")
            score -= 0.1

    # Check prompt_optimizer for probe feedback merge
    if "core/prompt_optimizer.py" in files:
        curr_po = get_file_content_at_ref("core/prompt_optimizer.py", head)
        if "merge_probe_feedback" not in curr_po:
            issues.append("⚠️  prompt_optimizer 中 merge_probe_feedback() 被移除，探测-反馈闭环断裂")
            score -= 0.25

    score = max(0.0, score)
    if not issues:
        return DimensionResult("AI 可见性探测", True, score, "探测字段完整可追踪。")
    return DimensionResult(
        "AI 可见性探测", score >= 0.5, score,
        "\n".join(issues)
    )


def check_knowledge_base(files: list[str], base: str, head: str) -> DimensionResult:
    """
    Supplementary check: Knowledge base integrity.
    Detects if .md content files in knowledge-base/ were deleted.
    """
    kb_files = [f for f in files if f.startswith(KNOWLEDGE_BASE_DIR)]
    if not kb_files:
        return DimensionResult(
            "知识库完整性", True, 1.0,
            "knowledge-base 目录无变更。"
        )

    issues = []
    score = 1.0

    for f in kb_files:
        # Check if the file was deleted (not just modified)
        try:
            curr = get_file_content_at_ref(f, head)
            if not curr:
                issues.append(f"❌ 知识库文件被删除: {f}")
                score -= 0.4
                continue
        except Exception:
            issues.append(f"❌ 知识库文件不可读: {f}")
            score -= 0.3
            continue

        # For .md files, check structural integrity
        if f.endswith(".md"):
            curr_lines = len(curr.split("\n"))
            prev = get_file_content_at_ref(f, base)
            prev_lines = len(prev.split("\n")) if prev else 0
            if curr_lines < prev_lines * 0.5:
                issues.append(f"⚠️  {f} 内容大幅缩减（{prev_lines} → {curr_lines} 行）")
                score -= 0.2

    score = max(0.0, score)
    if not issues:
        return DimensionResult("知识库完整性", True, score, "知识库文件完整。")
    return DimensionResult(
        "知识库完整性", score >= 0.5, score,
        "\n".join(issues)
    )


# ═══════════════════════════════════════════
#  Orchestrator
# ═══════════════════════════════════════════

class ReviewReport:
    def __init__(
        self,
        dimensions: list,
        overall_pass: bool,
        overall_score: float,
        blocking_count: int,
        warning_count: int,
        changed_files: list,
        summary: str,
    ):
        self.dimensions = dimensions
        self.overall_pass = overall_pass
        self.overall_score = overall_score
        self.blocking_count = blocking_count
        self.warning_count = warning_count
        self.changed_files = changed_files
        self.summary = summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_pass": self.overall_pass,
            "overall_score": self.overall_score,
            "blocking_count": self.blocking_count,
            "warning_count": self.warning_count,
            "changed_files": self.changed_files,
            "summary": self.summary,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }

    def to_markdown(self) -> str:
        lines = [
            "# GitGeo GEO PR Review Report",
            "",
            f"**Overall**: {'✅ PASS' if self.overall_pass else '❌ BLOCKED'} "
            f"(score: {self.overall_score:.2f}, "
            f"blocking: {self.blocking_count}, warnings: {self.warning_count})",
            "",
            f"**Changed files** ({len(self.changed_files)}):",
        ]
        for f in self.changed_files[:20]:
            lines.append(f"- `{f}`")
        if len(self.changed_files) > 20:
            lines.append(f"- ... and {len(self.changed_files) - 20} more")
        lines.append("")
        lines.append("## Dimension Results")
        lines.append("")
        lines.append("| Dimension | Result | Score | Detail |")
        lines.append("|-----------|--------|-------|--------|")
        for d in self.dimensions:
            icon = "✅" if d.passed else ("🔴" if d.blocking else "⚠️")
            detail_short = d.detail.split("\n")[0][:80] if d.detail else "-"
            lines.append(f"| {icon} {d.name} | {'PASS' if d.passed else 'BLOCKED' if d.blocking else 'WARN'} | {d.score:.2f} | {detail_short} |")
        lines.append("")
        lines.append("## Details")
        lines.append("")
        for d in self.dimensions:
            if not d.passed:
                lines.append(f"### {'🔴' if d.blocking else '⚠️'} {d.name}")
                lines.append(d.detail)
                lines.append("")
        return "\n".join(lines)

    def to_gh_annotation(self) -> str:
        """Generate GitHub Actions annotation output."""
        lines = []
        for d in self.dimensions:
            if d.blocking:
                for detail_line in d.detail.split("\n"):
                    lines.append(f"::error title=GEO::{d.name}: {detail_line}")
            elif not d.passed:
                for detail_line in d.detail.split("\n"):
                    lines.append(f"::warning title=GEO::{d.name}: {detail_line}")
        if not self.overall_pass:
            lines.append(
                f"::error title=GEO Review Blocked::"
                f"GEO quality review blocked: {self.blocking_count} blocking issues, "
                f"{self.warning_count} warnings. Overall score: {self.overall_score:.2f}"
            )
        return "\n".join(lines)


def run_review(base: str = "HEAD~1", head: str = "HEAD") -> ReviewReport:
    """Run the full GEO PR review across all dimensions."""
    changed_files = get_changed_files(base, head)

    # Additional knowledge-base dimension
    all_dimensions: list[DimensionResult] = []
    all_dimensions.append(check_quality_score_degradation(changed_files, base, head))
    all_dimensions.append(check_content_structure(changed_files, base, head))
    all_dimensions.append(check_capability_references(changed_files, base, head))
    all_dimensions.append(check_prompt_drift(changed_files, base, head))
    all_dimensions.append(check_publish_config(changed_files, base, head))
    all_dimensions.append(check_probe_tracking(changed_files, base, head))
    all_dimensions.append(check_knowledge_base(changed_files, base, head))

    # Calculate overall
    overall_score = sum(d.score for d in all_dimensions) / len(all_dimensions)
    blocking = sum(1 for d in all_dimensions if d.blocking)
    warnings = sum(1 for d in all_dimensions if not d.passed and not d.blocking)
    overall_pass = blocking == 0

    # Build summary
    if overall_pass:
        summary = f"✅ 全部 {len(all_dimensions)} 个维度通过审查（GEO 质量无退化）"
    else:
        parts = []
        if blocking:
            parts.append(f"{blocking} 个阻断项")
        if warnings:
            parts.append(f"{warnings} 个警告项")
        parts.append(f"综合评分 {overall_score:.2f}")
        summary = f"❌ 审查未通过：{'，'.join(parts)}"

    return ReviewReport(
        dimensions=all_dimensions,
        overall_pass=overall_pass,
        overall_score=overall_score,
        blocking_count=blocking,
        warning_count=warnings,
        changed_files=changed_files,
        summary=summary,
    )


# ═══════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="GitGeo GEO PR Review Bot",
    )
    parser.add_argument("--base", default="HEAD~1", help="Base ref to compare from")
    parser.add_argument("--head", default="HEAD", help="Head ref to compare to")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--gh-annotations", action="store_true", help="Output GitHub Actions annotations")
    parser.add_argument("--output", default=None, help="Write report to file")
    parser.add_argument("--ci", action="store_true", help="CI mode: exit 1 on block")
    args = parser.parse_args()

    report = run_review(args.base, args.head)

    if args.gh_annotations:
        print(report.to_gh_annotation())

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(report.to_markdown())

    if args.output:
        Path(args.output).write_text(report.to_markdown(), encoding="utf-8")

    if args.ci and report.blocking_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
