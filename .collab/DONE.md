# DONE — frontend_next 干净收编完成

## 完成项

1. ✅ `@saasfly/ui` → `@/components/ui/` 全部替换
2. ✅ `cn` 统一从 `@/lib/utils` 导入
3. ✅ `badge.tsx` 本地组件已创建（5 variants: default/outline/success/warning/danger）
4. ✅ probe 页面 JSX 修复 + 去敏（品牌→通用，emoji→lucide）
5. ✅ models 页面去敏（DeepSeek→OpenAI+Anthropic）
6. ✅ feedback 页面去敏（PCB→通用，DeepSeek/Kimi→Provider A/B）
7. ✅ knowledge 页面去敏
8. ✅ articles/keywords/publications/capabilities/runs 类型修复
9. ✅ root layout.tsx 已创建（含 <html><body>）
10. ✅ globals.css + tailwind + postcss 配置就绪
11. ✅ `npm run build` 通过（15 页全部编译成功）
12. ✅ `saasfly/` 和 `admin-panel/` 已删除

## 构建验证

```bash
cd frontend_next && npm run build
# ○ All 15 pages compiled successfully
# ○ First Load JS: 87.3 kB
```

## 启动命令

```bash
cd frontend_next
npm run dev
# → http://localhost:3000/admin/dashboard
```

## 截图清单（Codex 负责）

以下页面需要视觉验收并截图到 `docs/images/screenshots/`：

| 页面 | URL | 状态 |
|------|-----|------|
| 仪表盘 | /admin/dashboard | ✅ 等待 API 数据 |
| 文章管理 | /admin/articles | ✅ |
| 关键词 | /admin/keywords | ✅ |
| 能力库 | /admin/capabilities | ✅ |
| 发布中心 | /admin/publications | ✅ |
| 运行记录 | /admin/runs | ✅ |
| 系统状态 | /admin/system | ✅ |
| 知识库 | /admin/knowledge | ✅ |
| AI 探测 | /admin/probe | ✅ |
| 反馈闭环 | /admin/feedback | ✅ |
| 素材库 | /admin/materials | ✅ |
| 提示词库 | /admin/prompts | ✅ |
| 模型配置 | /admin/models | ✅ |
| 任务调度 | /admin/tasks | ✅ |
