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

---

## TASK #4 补充 — Codex 产品/用户验收意见交给 Worker

用户明确要求：Codex 不继续直接做实现，回到产品部门 / 用户视角 / review 角色；代码实现、构建、截图和清理由 Claude Code Worker 完成。

### 当前验收结论

`frontend_next/` 的方向是对的：148KB 的干净抽取比完整 `saasfly/` 模板健康很多，视觉也明显比旧 `frontend_v2` 更适合作为 gitgeo 正式前端。

但现在还不能进入截图和 README 更新阶段，因为存在几个会影响构建和开源质量的问题。

### Worker 必须处理的问题

1. `frontend_next` 仍残留 `@saasfly/ui` import。

证据：多个页面仍从 `@saasfly/ui/card`、`@saasfly/ui/button`、`@saasfly/ui/input`、`@saasfly/ui/tabs`、`@saasfly/ui/badge` 导入组件；`frontend_next/package.json` 没有 `@saasfly/ui` 包。

要求：全部改为本地组件导入，例如 `@/components/ui/card`、`@/components/ui/button`、`@/components/ui/input`、`@/components/ui/tabs`、`@/components/ui/badge`。

2. 本地 UI 组件的 `cn` 引用不完整。

证据：`frontend_next/src/components/ui/button.tsx` 仍从 `@saasfly/ui` 导入 `cn`；其他组件引用了不存在的 `./utils/cn`。项目实际已有 `frontend_next/src/lib/utils.ts`。

要求：统一从 `@/lib/utils` 导入 `cn`。

3. `Badge` 本地组件缺失。

证据：`feedback`、`knowledge`、`probe` 等页面使用了 `Badge`，但 `frontend_next/src/components/ui/` 初始没有 `badge.tsx`。

要求：补一个轻量本地 `Badge`，支持 default / outline / success / warning / danger 等基本状态即可。

4. `probe/page.tsx` 仍有去敏和 JSX 问题。

证据：页面仍出现 `PCB`、`DeepSeek`、`目标品牌`，还有 `⬜` 字符；并且 `<span>{CheckCircle2}</span>` 不是正确的 lucide 用法。

要求：改成 generic demo data：平台用 `Provider A/B/C` 或从配置读取；关键词用通用行业引用监测场景；图标使用 `<CheckCircle2 className="..." />` 和 `<XCircle className="..." />`，不要 emoji 或方块字符。

5. `models/page.tsx` 仍有硬编码 DeepSeek 默认。

证据：`deepseek-chat`、`DeepSeek`、`https://api.deepseek.com` 仍在新前端模型页中。

要求：默认展示 OpenAI-compatible / configurable provider 示例，真实 provider 从环境变量或 API 返回。

6. 需要跑通新前端构建。

当前 Codex 验证：在本地执行 `npm run build` 时，`next` 命令不存在，说明 `frontend_next` 依赖尚未安装。Worker 需要安装依赖后跑：

```bash
cd frontend_next
npm install
npm run build
```

如果构建失败，优先修构建错误，不要先截图。

7. 构建通过后再截图。

要求：启动 `frontend_next`，由 Codex 用 vision 验收和截图。Worker 先不要自行宣称截图完成；需要写 `DONE.md`，列出：

- 新前端目录结构
- 删除了哪些模板/产物
- 构建命令和结果
- 启动命令和本地 URL
- 已完成去敏项
- 仍需 Codex 视觉验收的页面列表

### Codex 已经做过的预检性改动

Codex 在转回产品/review 角色前，已经对 `frontend_next` 做过一小轮预检性修正：尝试把部分 `@saasfly/ui` import 改为本地 `@/components/ui/*`，并新增了 `frontend_next/src/components/ui/badge.tsx`。

Worker 可以保留、改进或重做这些修改；但不要把它们视为已完成验收。最终以 Worker 构建通过、DONE.md 和 Codex 视觉复验为准。

### Codex 截图前置验证结果

Codex 已安装依赖并尝试构建/启动 `frontend_next`，用于帮助 Worker 做截图。当前不能截图交付，存在以下 blocker：

1. `npm run build` 失败。

构建结果：

```text
✓ Compiled successfully
Linting and checking validity of types ...
Failed to compile.

./src/app/admin/(dashboard)/articles/page.tsx:21:61
Type error: Type 'string | undefined' is not assignable to type 'string'.
```

原因：`api.articles.list()` 的参数类型是 `Record<string, string>`，但页面传入了 `{ query: q || undefined, status: sf || undefined }`。Worker 需要在 API client 层支持 optional params，或页面层过滤 undefined。

2. Dev server 能启动，但页面被 Next 错误遮罩挡住，不能截图。

访问 `http://127.0.0.1:5175/admin/dashboard` 后，Chrome 截图显示：

```text
Missing required html tags
The following tags are missing in the Root Layout: <html>, <body>.
```

Worker 需要补齐 `frontend_next/src/app/layout.tsx` 的 root layout，必须返回 `<html lang="zh-CN"><body>...</body></html>`，并确保全局 CSS 正常加载。

3. 页面样式未完全应用，视觉不能验收。

截图中侧栏和按钮呈现为浏览器默认样式，说明 root layout / globals.css / Tailwind 或组件样式链路未正确生效。Worker 修完 root layout 后，需要再次自测页面样式。

4. Dashboard 显示 `Failed to fetch`。

这是后端未启动或 API base 未配置导致。截图可以接受 demo/mock 状态，但 README 截图不能展示错误态。Worker 需要提供以下二选一：

- 本地截图时启动后端 API，并确保 dashboard/articles 等页面有真实数据。
- 或在 `frontend_next` 提供 demo fallback/mock data，让截图状态健康。

5. 仍有去敏残留。

`frontend_next/src/app/admin/(dashboard)/feedback/page.tsx` 仍有 `PCB` 和 `DeepSeek`。Worker 需要改成 generic demo data 或可配置平台名称。

6. 截图流程暂停。

Codex 已停止本轮 `frontend_next` dev server。等 Worker 修复以上 blocker，并写 `DONE.md` 告知启动命令和 URL 后，Codex 再负责打开浏览器、视觉验收、覆盖 `docs/images/screenshots/`。
