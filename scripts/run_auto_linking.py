"""
手动内链脚本 (Manual Auto-Linking Runner)
==========================================
手动触发一次自动内链处理。
将扫描所有 Pending 状态文章，插入内部链接。

使用方法：
    python scripts/run_auto_linking.py
"""

from core.link_manager import LinkManager

if __name__ == "__main__":
    linker = LinkManager()
    linker.run_auto_linking()
