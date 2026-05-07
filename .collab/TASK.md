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
