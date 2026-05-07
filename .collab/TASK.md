# TASK #5 — 超越 GEOFlow · Claude + Codex 持续协作

## 目标
gitgeo → GitHub GEO 品类第一名（当前 GEOFlow 1438 ⭐）

## 独有武器（GEOFlow 没有）
- **AI 探测**: 检测 DeepSeek/Kimi/豆包 品牌可见性
- **Prompt 闭环**: 探测→分析→优化→再生
- **9 维质检**: 文章质量自动化
- **多平台发布**: 知乎/微信 + 适配器

## Phase 1: README 决胜（今天）
- 14 张截图展示所有页面
- 竞品对比表突出独有武器
- 中英双语
- Demo 模式不需要 API key

## Phase 2: 核心闭环可演示
- docker compose up → 1h 内看到探测结果
- 通用行业关键词种子

## Phase 3: 传播
- GitHub topics: generative-engine-optimization, geo, ai-seo
- 文章: "全球首个开源一站式GEO系统"
- 3 分钟 demo 视频

## Claude: 代码/API/CI/Docker/README
## Codex: 视觉/翻译/截图/GitHub配置/传播

---

## TASK #5A — Claude 执行：README 决胜补齐

Codex 已按 Phase 1 做完当前开源展示巡检。截图和新前端已经具备基础，但 README 仍是旧叙事。请 Claude 优先修改 README / README_EN / 配置文档，目标是让 GitHub 首页一打开就能看出 gitgeo 的差异化。

### Codex 巡检事实

- `docs/images/screenshots/` 当前有 14 张截图。
- `frontend_next/src/app/admin/**/page.tsx` 当前也是 14 个页面。
- `frontend_next` 技术栈是 Next.js 14 + React 18 + Tailwind + lucide，不是 Vue 3。
- `dashboard.png`、`articles.png`、`publications.png` 都已是健康 Demo Mode 截图。
- `probe.png` 和 `feedback.png` 最能体现 gitgeo 独有差异，应放在 README 更靠前的位置。

### README.md 必改

1. 删除旧前端口径：
   - 不再写 `Vue 管理后台`
   - 不再写 `12 页管理系统`
   - 不再把 `open http://localhost:8503` Streamlit 作为快速开始入口
   - 不再把 `open http://localhost:5173` Vue 作为主入口

2. 改成新前端口径：
   - `Next.js 管理后台`
   - `14 页管理系统`
   - `Demo Mode 无需 API key 即可浏览后台`
   - 本地前端入口写 `frontend_next` 和 `/admin/dashboard`

3. 截图区重排：
   - 第一屏优先放 `probe.png`（AI 探测）和 `feedback.png`（反馈闭环）
   - 然后放 `dashboard.png`
   - 再展示 `articles.png`、`publications.png`、`prompts.png`、`models.png`
   - 补齐 14 张截图路径列表，不再写“请补充实际截图”

4. 竞品对比表重写：
   - 对比对象明确为 `GEOFlow / 通用内容系统 / gitgeo`
   - 突出 GEOFlow 没有的独有武器：
     - AI visibility probing
     - Prompt feedback loop
     - 9-dimension quality scoring
     - multi-platform publishing adapters
     - Demo Mode admin without API key
   - 不要用太多 emoji；表格应专业、可验证。

5. 通用化与去敏：
   - README 不应再出现 `深亚电子`、`pcbshenya.com`
   - DeepSeek 只能作为 supported provider 示例之一，不能作为默认配置
   - `GEO_LLM_BASE_URL` 示例改为 OpenAI-compatible placeholder，例如 `https://your-openai-compatible-endpoint/v1`
   - `GEO_LLM_MODEL` 示例改为 `your-model-name`

6. 反馈闭环表达改写：
   - 不写“DeepSeek 提到我们品牌了吗?”
   - 改为“AI answer mentions target entity? includes citation-worthy evidence? source label hit?”
   - 中文可写：`AI 回答是否提及目标实体、是否引用权威来源、是否命中工程实践/官方文档/标准文档等标签`

### README_EN.md 必改

1. 与中文 README 信息同步。
2. 技术栈改成 Next.js admin，不再写 Vue/Element Plus。
3. 删除 Shenya/pcbshenya 致谢或改成匿名化 early industry validation。
4. 增加截图区，至少包含 `probe.png`、`feedback.png`、`dashboard.png`。
5. 增加 Demo Mode 说明。

### 配置与 Docker 文档待处理

1. `.env.example` 不应默认 `https://api.deepseek.com` 和 `deepseek-chat`。
2. `docker-compose.yml` 仍有 Streamlit 8503 服务和 deepseek 默认 fallback。若暂时保留 legacy，请在 README 明确它是 legacy，不作为主入口。
3. README 快速开始必须与实际 Docker / frontend_next 启动方式一致。

### GitHub topics 建议

请在 README 或发布 checklist 中建议仓库 topics：

- `generative-engine-optimization`
- `geo`
- `ai-seo`
- `llm-seo`
- `content-automation`
- `crewai`
- `fastapi`
- `nextjs`
- `rag`
- `prompt-engineering`

### 完成后

Claude 修改后请更新 `.collab/DONE.md`，列出：

- 修改了哪些 README/配置文件
- README 中截图顺序
- 是否仍保留 legacy Streamlit/Vue
- 是否已经去除 Shenya/pcbshenya
- 是否已经把默认 LLM 配置改为通用 OpenAI-compatible 模板

Codex 随后复审 README 渲染效果、英文质量、截图顺序和开源风险。

---

## TASK #6 — Claude 执行：核心功能闭环，不再继续 UI/README

用户已确认 UI 和 README 暂时按当前版本进入冻结状态。后续不要把主要时间继续花在 README 竞品表、截图排版或视觉文案上。当前目标切到可运行、可演示、可扩展的功能闭环。

### 产品目标

把 gitgeo 从“内容生成 + 两个硬编码发布渠道”升级为真正通用的 GEO 系统：

`行业画像 → 高权重站点筛选 → 平台适配器 → browser/API 发布 → AI 引用探测 → 证据标签分析 → Prompt 自迭代`

### P0 必做：行业驱动站点选择器

请新增通用模块，不要写死 PCB、知乎、微信：

1. 新增 `core/site_selector.py` 或等价模块。
2. 输入：行业、目标地区、内容类型、目标关键词、可用发布方式。
3. 输出：候选站点列表，每个站点包含：
   - `site_key`
   - `display_name`
   - `domain`
   - `channel_type`
   - `publish_method`: `api` / `browser` / `manual`
   - `authority_score`
   - `relevance_score`
   - `freshness_score`
   - `citation_potential_score`
   - `reason`
4. 站点权重必须可配置，建议放到 `config/site_profiles/*.yaml` 或数据库 seed，不要硬编码在服务层。
5. 内置几个通用 demo 行业即可，例如 `generic_b2b`、`software`、`manufacturing`，PCB 只能作为示例画像之一，不能作为默认内核。

### P0 必做：平台适配器注册表

当前 `backend/app/services/publications_service.py` 仍然把 `longform_channel -> zhihu`、`mobile_channel -> wechat` 写死。请重构为 registry：

1. 新增 `core/publishers/base.py`，定义统一接口：
   - `adapter_key`
   - `display_name`
   - `publish_method`
   - `supports_draft`
   - `ready`
   - `publish(title, content_md, metadata)`
   - `publish_and_go_live(title, content_md, metadata)`
2. 新增 `core/publishers/registry.py`，从配置注册 adapters。
3. 把 `ZhihuPublisher`、`WeChatPublisher` 包装/迁移为 registry adapter。
4. 增加 `BrowserPublisher` demo adapter：先不强求真实登录发布，但必须能产出“发布计划/草稿写入/待人工确认”的结构化结果。
5. `PublicationsService` 不再识别固定两条 channel，而是从 registry/site selector 获取 adapter。

### P1 必做：browser/API 发布器的安全边界

发布功能必须避免开源用户一跑就误发：

1. 默认 `publish_mode=draft`。
2. `go_live=true` 时必须检查环境变量，例如 `GEO_ENABLE_LIVE_PUBLISH=true`，否则返回明确错误。
3. browser 发布器必须支持 dry-run，输出目标 URL、标题、摘要、待填写字段，不自动提交最终发布按钮。
4. 所有外部发布结果必须写入 `article_publications`，保留 request/response payload，便于追踪。

### P1 必做：引用监测结果反哺 Prompt

现有 `ActiveProber` 和 `PromptOptimizer` 已有雏形，请把它们串成可运行闭环：

1. 新增 service/job：对指定关键词和平台执行 probe。
2. 把 `mentioned/cited/evidence_labels/source_hits/missing_labels/coverage_score` 持久化。
3. 下一轮生成文章时能够读取历史反馈，注入 prompt context。
4. 新增最小 API 或 CLI demo：
   - 输入 keyword
   - 生成/读取文章
   - 模拟或真实 probe
   - 生成 prompt feedback
   - 下一轮 prompt 能看到反馈文本
5. Demo 模式可以用 fixture，不依赖真实 AI 平台登录。

### P1 必做：测试

请至少补这些测试：

1. site selector 根据行业返回不同站点排序。
2. registry 能注册并发现 zhihu/wechat/browser adapters。
3. `PublicationsService` 不再只接受 `longform_channel/mobile_channel`。
4. live publish guard 未开启时拒绝真实发布。
5. prompt feedback 能把 missing labels 注入下一轮 prompt context。

### Codex 验收标准

Claude 完成后请在 `.collab/DONE.md` 写：

- 新增/修改文件列表。
- 如何运行 demo。
- 哪些功能是真实外部调用，哪些是 dry-run/demo fixture。
- 测试命令和结果。
- 仍未完成的风险点。

Codex 将从产品视角复验：

- 是否真的通用，而不是把 PCB/知乎/微信换个名字继续写死。
- 是否能解释每个行业为什么选择某些高权重站点。
- 是否有安全 dry-run 边界。
- 是否能形成“探测数据 → 证据标签 → prompt 更新”的闭环。

---

## TASK #5B — Claude 执行：README 截图区返修

用户在 GitHub 移动端截图中确认了一个展示问题：README 的“截图”区域现在主要显示 `probe.png`、`feedback.png` 等文件名表格，不是视觉截图画廊。这个会让访问者误以为仓库没有真正展示产品界面。

### 必改

1. 把 README.md 的 `## 截图` 从路径表改成真正的图片画廊。
2. 14 个页面都要以图片方式渲染，不要只列文件名。
3. 第一屏优先展示最能说明差异化的三张：
   - `docs/images/screenshots/probe.png`
   - `docs/images/screenshots/feedback.png`
   - `docs/images/screenshots/dashboard.png`
4. 后面继续展示：
   - `articles.png`
   - `keywords.png`
   - `capabilities.png`
   - `publications.png`
   - `runs.png`
   - `system.png`
   - `knowledge.png`
   - `materials.png`
   - `prompts.png`
   - `models.png`
   - `tasks.png`
5. 移动端 GitHub 可读性优先，建议用简单的 Markdown：
   - `### AI 探测`
   - `![AI 探测](docs/images/screenshots/probe.png)`
   - 不要依赖复杂 HTML 表格。
6. 可以保留一个很短的“截图文件位于 docs/images/screenshots/”说明，但不能让文件名表成为主要展示。

### 完成后

Claude 请在 `.collab/DONE.md` 写清：

- README 截图区是否已从路径表改为 14 张真实图片。
- 截图展示顺序。
- 是否同步 README_EN.md，如果未同步请说明原因。
