# gitgeo 超越 GEOFlow 工作汇报 — 给 Codex

## 背景
gitgeo 是全球最早的开源一站式 GEO（生成式引擎优化）系统（2026.04 首发），对标项目是 GEOFlow（PHP Laravel，1438 ⭐）。

## 已完成的"超越"工作

### 1. 一键部署
`docker compose up -d` → 自动建表 + 导入种子关键词 + 开始生产。GEOFlow 需要手动配 PHP/PostgreSQL/Redis。

### 2. AI 提供商标配解锁
环境变量 `GEO_LLM_API_KEY/BASE_URL/MODEL` 支持任意 OpenAI 兼容 API（DeepSeek/OpenAI/Groq/vLLM），不再硬编码供应商。

### 3. 品牌去敏
所有"深亚电子"/"pcbshenya.com"从代码中清除，改用 `GEO_SITE_NAME/DOMAIN/ORG_NAME` 环境变量。

### 4. 前端重写
Element Plus → Naive UI，新增 4 个管理页面（素材库/提示词库/模型配置/任务调度），侧边栏分为监控/管理/内容运营/分发 4 组。12 页管理系统。

### 5. 独有能力（GEOFlow 没有）
- **AI 平台主动探测**：DeepSeek/Kimi/豆包 品牌可见性追踪
- **9 维质检 + 自动返修**：文章质量闭环
- **Prompt 反馈闭环**：探测→分析→优化→再生
- **能力记忆层**：结构化品牌参数库
- **多平台外部发布**：知乎/微信 + 可扩展适配器

## 当前待办（需要你审视）

1. **README 截图**：8 张管理后台截图在 `docs/images/screenshots/`，需要确认是否展示完整功能
2. **前端 UI**：当前使用 Naive UI，但视觉上线还没达到专业水准。已安装 UI/UX Pro Max skill（74.8K ⭐）可辅助设计
3. **前端构建**：`npm run build` 在 CI 通过，但 dev 模式有些页面因缺少后端 API 显示空状态
4. **发布器**：知乎/搜狐/百家号的自动发布被反爬拦截，CloakBrowser 是候选方案

## 你的任务

1. 审视 `README.md` — 定位是否清晰、截图是否到位、和 GEOFlow 的对比是否有说服力
2. 审视前端代码 `frontend_v2/` — 当前 Naive UI 方案是否合理，视觉能否再提升
3. 审视架构 `core/` — 有没有冗余或可优化的模块
4. 把审视结果写到 `REVIEW.md`，列出优先级（P0/P1/P2）
