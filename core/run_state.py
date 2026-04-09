"""
运行态上下文
============
用于在同一进程内把本次文章生成的入库结果回传给调用方。

当前系统的批量生产和 Dashboard 手动生产都是单进程、单关键词串行执行，
因此使用进程内状态即可避免再通过“最新草稿”反推文章 ID。
"""

from __future__ import annotations


_current_run_id: str | None = None
_saved_article_results: dict[str, dict] = {}


def set_current_run_id(run_id: str) -> None:
    """标记当前文章生成 run_id。"""
    global _current_run_id
    _current_run_id = run_id


def clear_current_run_id() -> None:
    """清除当前文章生成 run_id。"""
    global _current_run_id
    _current_run_id = None


def clear_saved_article_result(run_id: str) -> None:
    """清除历史保存结果，避免读到上一次的残留数据。"""
    _saved_article_results.pop(run_id, None)


def record_saved_article_result(result: dict) -> None:
    """记录当前 run_id 对应的文章保存结果。"""
    if _current_run_id:
        _saved_article_results[_current_run_id] = dict(result)


def pop_saved_article_result(run_id: str) -> dict | None:
    """取出并删除某次 run 的文章保存结果。"""
    return _saved_article_results.pop(run_id, None)
