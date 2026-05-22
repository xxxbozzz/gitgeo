# gitgeo

> 🌍 **开源一站式 GEO（生成式引擎优化）引擎** — 从关键词发现、9 维评分、AI 可见性探测到多平台自动发布，全流程工程化。

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%2B-336791)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_async-red)](https://www.sqlalchemy.org/)
[![CloakBrowser](https://img.shields.io/badge/CloakBrowser-anti_detect-black)](https://github.com/CloakHQ/CloakBrowser)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://docs.docker.com/compose/)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF)](https://github.com/xxxbozzz/gitgeo/actions)
[![Tests](https://img.shields.io/badge/tests-12%2F12_passed-brightgreen)](.)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Email](https://img.shields.io/badge/Email-huangkuifu010%40gmail.com-blue)](mailto:huangkuifu010@gmail.com)

> 🇬🇧 [English](README_EN.md) | 🇨🇳 简体中文

---

## 它是什么

gitgeo 是一套**完整的 GEO 工作流引擎**。大多数内容系统止步于「关键词 → 生成 → 发布」。gitgeo 多做了一步：**测量你的内容是否真的被 AI 引用，把测量结果反哺给下一轮生成。**

本项目源于[**四川深亚电子科技有限公司**](https://www.pcbshenya.com)的真实 GEO 业务需求。📧 [huangkuifu010@gmail.com](mailto:huangkuifu010@gmail.com)

```
关键词发现 → 证据采集 → Prompt 组装 → 9 维质检 → AI 探测（4 平台 × 2 端）
    → 反馈写回 → 自动内链 → 多平台发布 → 审计追踪
```

---

## 核心能力

### AI 可见性探测（4 平台 × 2 端）

DeepSeek / 豆包 / Kimi / 元宝（混元），桌面 + 移动端各探测一次。每篇文章 8 个探测通道，检测品牌提及、引用线索、证据标签命中率。

```python
from core.active_prober import ActiveProber
prober = ActiveProber()
results = prober.probe_all("PCB阻抗控制")  # 8 个通道同时跑
```

### Prompt 反馈闭环

探测结果自动提取「工程实践 / 官方文档 / 标准文档」等引用标签，未命中的标签写回为下一轮 Prompt 的优化约束。

### 9 维质检 + 自动返修

字数深度、H2 结构、数据表格、FAQ、参考文献、首句定义、违禁词、逻辑链、标题质量。低于 80 分自动返修，最多 3 轮。

### Publish Layer — 反检测多平台发布

基于 CloakBrowser（Playwright + 57 C++ patches）的反检测浏览器引擎。加新平台 = 写一个 Adapter 类，4 个方法。

```python
class MyPlatformAdapter(PlatformAdapter):
    platform_key = "myplatform"
    async def login(self, engine, *, headless=False): ...
    async def check_auth(self, engine): ...
    async def publish(self, engine, article): ...
    async def get_status(self, engine, article_id): ...
```

已实现：知乎、微信公众号、DEV.to、Telegraph、DryRun。登录态保存到 `config/auth/`（已加入 .gitignore）。

### 能力记忆层

品牌可验证能力参数的结构化存储与引用溯源。12 组能力条目 + 11 条证据来源，生成时自动查询。

### 管理后台

Next.js 14 页管理系统，亮色/暗色双主题。Demo Mode 无需 API Key。

---

## 技术栈

| 层 | 技术 |
|---|------|
| 数据库 | PostgreSQL 17 + pgvector |
| ORM | SQLAlchemy 2.0 async |
| 后端 | FastAPI (Python 3.12+) + 27 条 API 路由 |
| AI 编排 | 6 Agent 流水线（Scout → Writer → Checker → Fixer → Linker → Prober） |
| LLM | OpenAI 兼容 API（DeepSeek v4-pro / GPT-4 / Claude） |
| 浏览器引擎 | CloakBrowser（反检测 Playwright） |
| 前端 | Next.js 14 + React 18 + Tailwind CSS |
| 向量存储 | ChromaDB |
| 测试 | pytest + httpx + AsyncMock（12/12 passed） |
| CI/CD | GitHub Actions（PostgreSQL service + test + GEO review） |
| 部署 | Docker Compose |

---

## 5 分钟快速开始

```bash
git clone https://github.com/xxxbozzz/gitgeo.git && cd gitgeo
cp .env.example .env
# 编辑 .env: 填入 GEO_LLM_API_KEY

docker compose up -d
```

首次启动自动初始化 PostgreSQL 表结构 + 导入种子关键词。

**本地开发（不需要 Docker）：**

```bash
# 需要本地 PostgreSQL 17+
brew install postgresql@17 && brew services start postgresql@17
createdb geo_engine
psql geo_engine -f database/init_postgres.sql

pip install -r requirements.txt
GEO_LLM_API_KEY=sk-xxx uvicorn backend.app.main:app --port 8001
```

**跑测试：**

```bash
# 本地（mock DB，6 passed, 6 route-check）
pytest backend/tests/ -v

# 真 PostgreSQL（12/12 passed）
GEO_TEST_DB=1 DB_HOST=localhost DB_USER=geo_app DB_PASSWORD=xxx pytest backend/tests/ -v
```

## Docker 镜像

已构建并推送至 GitHub Container Registry：

```bash
docker pull ghcr.io/xxxbozzz/gitgeo:latest
```

镜像包含（4.3GB，全预装，拉取即用）：
- CloakBrowser 反检测 Chromium（140MB 预下载）
- Playwright Chromium + Firefox + WebKit
- PostgreSQL 客户端工具
- 全部 Python 依赖

或通过 Docker Compose 使用完整环境：

```bash
docker compose up -d
# PostgreSQL + Backend (FastAPI :8001) + Dashboard (Streamlit :8503)
# + ChromaDB + Scheduler — 全部就绪
```

---

## 管理后台预览

![AI 探测](docs/images/screenshots/probe.png)
![反馈闭环](docs/images/screenshots/feedback.png)
![仪表盘](docs/images/screenshots/dashboard.png)
![文章管理](docs/images/screenshots/articles.png)
![关键词](docs/images/screenshots/keywords.png)
![能力库](docs/images/screenshots/capabilities.png)
![发布中心](docs/images/screenshots/publications.png)
![运行记录](docs/images/screenshots/runs.png)
![系统状态](docs/images/screenshots/system.png)
![知识库](docs/images/screenshots/knowledge.png)
![素材库](docs/images/screenshots/materials.png)
![提示词库](docs/images/screenshots/prompts.png)
![模型配置](docs/images/screenshots/models.png)
![任务调度](docs/images/screenshots/tasks.png)

---

## 配置

```bash
# LLM（必填）
GEO_LLM_API_KEY=sk-xxx
GEO_LLM_BASE_URL=https://api.deepseek.com
GEO_LLM_MODEL=deepseek-v4-pro

# 数据库
DB_HOST=localhost          # Docker 内用 postgres
DB_PORT=5432
DB_USER=geo_app
DB_PASSWORD=change-this-password
DB_NAME=geo_engine

# 品牌（可选）
TARGET_ENTITY_NAME=我的品牌
GEO_ORG_NAME=我的品牌

# 发布（可选）
WECHAT_APP_ID=xxx
WECHAT_APP_SECRET=xxx
GEO_ENABLE_LIVE_PUBLISH=false   # 安全阀，必须显式开启
```

---

## 工程化指标

| 指标 | 值 |
|------|-----|
| API 路由 | 27 条（8 个模块） |
| 数据库表 | 12 张（ORM 模型） |
| Repository | 7 个 |
| 测试 | 12/12 passed（0.87s） |
| CI | GitHub Actions（PostgreSQL + test + GEO review） |
| MySQL 残留 | 0（全项目已迁移） |
| 发布适配器 | 5 个（知乎/微信/DEV.to/Telegraph/DryRun） |
| 探测通道 | 8 个（4 平台 × 2 端） |

---

## 文档

- [系统架构](docs/system_structure.md)
- [AI 反馈闭环](docs/ai_feedback_loop.md)
- [Prompt 流水线](docs/prompt_pipeline_guide.md)
- [Prompt 编写指南](docs/prompt_creator_guide.md)

## 致谢

本项目在早期得到了[**四川深亚电子科技有限公司**](https://www.pcbshenya.com)的业务场景验证支持。

## 许可

MIT © [xxxbozzz](https://github.com/xxxbozzz)
