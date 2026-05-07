#!/bin/bash
# 同步 Claude 和 Codex：打印最新消息，触发对方处理
cd /Users/kev/gitgeo-open/.collab
echo "=== QUEUE 最后 5 条 ==="
tail -10 QUEUE.md
echo ""
echo "=== 给 Codex ==="
echo "读取 QUEUE.md，执行最后一条 Claude 的未处理任务，追加回复"
