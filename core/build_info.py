"""
构建版本信息
============
部署脚本会在服务器项目根目录生成 build_info.json。
运行时可读取该文件，方便在日志和 Dashboard 中确认线上版本。
"""

from __future__ import annotations

import json
import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_INFO_FILE = os.path.join(PROJECT_ROOT, "build_info.json")


def load_build_info() -> dict:
    """读取部署版本信息。"""
    try:
        with open(BUILD_INFO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def format_build_label() -> str:
    """格式化用于日志和 UI 的构建标签。"""
    info = load_build_info()
    if not info:
        return "未记录"

    branch = info.get("git_branch") or "unknown"
    commit = info.get("git_commit_short") or info.get("git_commit") or "unknown"
    deployed_at = info.get("deployed_at") or "unknown"
    dirty = " dirty" if info.get("git_dirty") else ""
    return f"{branch}@{commit}{dirty} | deployed {deployed_at}"
