# Codex ↔ Claude Code 协作协议

## 工作流
1. Codex 写 `TASK.md` → Claude Code 读取并执行
2. Claude Code 写 `DONE.md` → Codex 读取，用 vision/CU 验证
3. Codex 验证通过 → 标记 `APPROVED.md`
4. Codex 验证不通过 → 把问题写回 `TASK.md`，循环

## 角色分工
- **Codex**: 需求定义 / UI排版 / 视觉验证 / Word & 桌面操作
- **Claude Code**: 代码实现 / 管线 / 后端 / 批量操作 / git

## 文件约定
- `TASK.md` - Codex 发出的任务指令
- `DONE.md` - Claude Code 完成后的报告（含文件路径、改动说明）
- `APPROVED.md` - Codex 验证通过标记
- `FEEDBACK.md` - Codex 的视觉反馈（需要改进的地方）

## 规则
- 每次只处理一个任务
- 完成状态必须带文件路径
- 不要覆盖对方的文件，只追加
