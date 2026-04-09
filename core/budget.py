"""
月度 Token 用量统计器 (Monthly Token Tracker)
==============================================
仅统计记录，不做限制。用于 Dashboard 展示和成本回顾。

用法:
    from core.budget import tracker
    tracker.record(input_tokens=5000, output_tokens=3000, label="repair:阻抗控制")
    print(tracker.monthly_summary())
"""

import json
import os
from datetime import date, datetime
from pathlib import Path


# DeepSeek-V3 定价 (¥/1M tokens)
PRICE_INPUT_PER_M  = 1.00
PRICE_OUTPUT_PER_M = 2.00


class MonthlyTokenTracker:
    """
    按月统计 Token 用量。数据持久化到 token_usage.json。
    每月 1 号自动归档上月数据。
    """

    def __init__(self, data_file: str | None = None):
        self.data_file = Path(data_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "token_usage.json",
        ))
        self._data = self._load()

    def _load(self) -> dict:
        current_month = date.today().strftime("%Y-%m")
        if self.data_file.exists():
            try:
                raw = json.loads(self.data_file.read_text(encoding="utf-8"))
                if raw.get("current_month") == current_month:
                    return raw
                # 新月 → 归档旧月
                archive = raw.get("archive", {})
                old_month = raw.get("current_month", "unknown")
                archive[old_month] = {
                    "input_tokens": raw.get("input_tokens", 0),
                    "output_tokens": raw.get("output_tokens", 0),
                    "total_cost_cny": raw.get("total_cost_cny", 0),
                    "calls": raw.get("calls", 0),
                }
                return self._new_month(current_month, archive)
            except Exception:
                pass
        return self._new_month(current_month)

    @staticmethod
    def _new_month(month: str, archive: dict | None = None) -> dict:
        return {
            "current_month": month,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost_cny": 0.0,
            "calls": 0,
            "archive": archive or {},
        }

    def _save(self):
        try:
            self.data_file.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def record(self, input_tokens: int, output_tokens: int, label: str = "") -> float:
        """记录一次调用，返回本次费用 (¥)"""
        self._data = self._load()
        cost = (
            input_tokens  / 1_000_000 * PRICE_INPUT_PER_M +
            output_tokens / 1_000_000 * PRICE_OUTPUT_PER_M
        )
        self._data["input_tokens"]   += input_tokens
        self._data["output_tokens"]  += output_tokens
        self._data["total_cost_cny"] += cost
        self._data["calls"]          += 1
        self._save()
        return cost

    def monthly_summary(self) -> str:
        """本月摘要"""
        d = self._data
        return (
            f"[{d['current_month']}] "
            f"调用 {d['calls']} 次 | "
            f"输入 {d['input_tokens']:,} / 输出 {d['output_tokens']:,} tokens | "
            f"费用 ¥{d['total_cost_cny']:.4f}"
        )

    def get_stats(self) -> dict:
        """返回当月统计数据（供 Dashboard 使用）"""
        self._data = self._load()
        return {
            "month": self._data["current_month"],
            "input_tokens": self._data["input_tokens"],
            "output_tokens": self._data["output_tokens"],
            "total_cost_cny": round(self._data["total_cost_cny"], 4),
            "calls": self._data["calls"],
            "archive": self._data.get("archive", {}),
        }


# 全局单例
tracker = MonthlyTokenTracker()

# 向后兼容旧导入
budget = tracker
