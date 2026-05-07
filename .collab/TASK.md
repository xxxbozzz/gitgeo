# TASK #4 — 给 Claude Code Worker：采用 saasfly admin 前端并干净收编

## 背景
用户确认：采用 `saasfly` 里的新 admin 前端视觉方向作为 gitgeo 的正式前端，不再把它迁回旧 `frontend_v2`。

真正有价值的前端在：

`saasfly/apps/nextjs/src/app/admin/(dashboard)/`

不要使用 `admin-panel/` 的 Next 默认欢迎页；不要把完整 `saasfly` 模板仓库、依赖、构建产物和无关 SaaS 模块原样提交。

## 任务
1. 将 `saasfly/apps/nextjs/src/app/admin/(dashboard)/` 抽成 gitgeo 的正式前端。
2. 建议新目录名：`frontend/` 或 `frontend_next/`，二选一；不要再维护 `admin-panel/`。
3. 只保留 gitgeo admin 必需内容：
   - admin layout
   - dashboard / articles / keywords / capabilities / publications / runs / system
   - probe / feedback
   - materials / prompts / models / tasks / knowledge
   - shared UI components
   - API client
   - theme tokens / Tailwind config
4. 删除或不要提交以下内容：
   - `saasfly/.git`
   - `saasfly/node_modules`
   - `saasfly/apps/nextjs/.next`
   - `saasfly/.env.local`
   - Stripe / Clerk / NextAuth / billing / marketing / blog / docs / pricing / unrelated SaaS packages
   - `admin-panel/` 默认脚手架
5. 去敏和通用化：
   - DeepSeek 只能作为示例平台之一，不能写死为默认平台
   - PCB / 深亚 / 目标品牌示例改为 generic demo data 或可配置行业 demo
   - 删除 UI 中的 emoji，用 lucide/icons 统一
   - API base/model/provider 从环境变量或配置接口读取
6. 修复页面完整度：
   - `models` / `prompts` / `tasks` 不允许停留在“即将上线”
   - `layout` 中重复的“效果”分组要合并
   - 所有页面要有 loading / empty / error 状态
7. 更新文档：
   - README 快速开始改成新前端启动方式
   - Docker/compose 如需改端口同步更新
   - 截图覆盖 `docs/images/screenshots/`
   - 新增或更新 `DONE.md`，列出改动文件、验证命令、截图路径

## Claude Code 的角色
Claude Code 负责收编、清理、接 API、构建、截图、文档和 CI。Codex 负责用用户视角复审 UI 质量、截图和开源风险。
