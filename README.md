# GEO Engine

[English README](./README_EN.md)

Open Source Watermark: [`github.com/xxxbozzz`](https://github.com/xxxbozzz)

通用的 GEO / AEO 内容生产、评分、反馈与分发引擎。

一句话理解：

这是一个把“行业输入 -> Prompt 编排 -> 文章生成 -> 质量评分 -> AI 可见性反馈 -> 渠道分发”串成工程闭环的开源系统骨架。

这个项目的重点不是“批量堆文章”，而是围绕可追溯证据、AI 可见性监测和 Prompt 自迭代，持续提升内容被搜索引擎、AI 助手和行业问答系统引用的概率。

## 项目声明

- 这是一个面向个人与小团队的开源 GEO 系统骨架，适合为非 GEO 公司进行个人化 GEO 推广、内容验证和方法论沉淀。
- 它不是某家 GEO 服务公司的官方产品，也不代表任何第三方 GEO 平台或营销公司的官方立场。
- 当前仓库重点公开的是系统结构、Prompt 链路、评分反馈闭环和渠道适配思路。

## 支持说明

- 本项目支持作为四川深亚电子相关 GEO 实践与内容推广的开源技术底座之一。
- 四川深亚电子官网：<https://www.pcbshenya.com/>
- 这里的支持说明用于说明适配与实践背景，不代表仓库中的所有通用能力仅限于单一行业。

## 它解决什么问题

很多内容系统只会做这几件事：

- 找关键词
- 生成文章
- 发布出去

但真正影响 AI 引用率的，通常是这些更底层的能力：

- 文章是否覆盖标准文档、官方文档、工程实践、测试数据、失效案例
- 文章是否明确写清适用边界、参数窗口和实施条件
- 发布后是否真的在 AI 平台里出现、被提及、被引用
- 监测结果是否能反哺下一轮 Prompt

GEO Engine 试图把上面这条链路工程化。

## 核心能力

- 关键词发现与 GEO gap 挖掘
- 证据型内容采集与结构化写作
- 文章质检、返修和去重
- AI 平台主动探测与可见性评分
- Prompt 自迭代与衍生关键词扩展
- 可替换的渠道适配与同步分发层

## 开源价值主张

如果你第一次打开这个仓库，只需要先记住这 3 件事：

- 这是什么：一个面向 GEO / AEO 工作流的内容系统骨架，而不是单纯的文章生成器
- 它解决什么：把“写文章”升级成“生成、评分、反馈、再生成、分发”的工程链路
- 最有价值的能力：Prompt 能进入闭环，被评分和监测结果持续修正

## 核心闭环

1. 发现关键词或内容空白。
2. 采集标准、官方资料、工程实践和验证证据。
3. 生成结构化文章并做质量检查。
4. 对已生成内容做“可引用性画像”分析。
5. 可选地到多个 AI 平台做主动探测。
6. 把监测结果写回反馈仓库。
7. 下一轮生成时，将反馈注入 Prompt。
8. 从高价值证据中自动扩展衍生关键词，例如：
   - `关键词 + 工程实践`
   - `关键词 + 官方文档解读`
   - `关键词 + 标准对照`

详细说明见 [系统结构总览](./docs/system_structure.md)、[AI 反馈闭环](./docs/ai_feedback_loop.md)、[自动化 Prompt 流水线指南](./docs/prompt_pipeline_guide.md)、[创作者 Prompt 构建指南](./docs/prompt_creator_guide.md) 和 [最小闭环 Demo](./docs/minimal_demo.md)。

## 当前目录

- `batch_generator.py`
  主生成入口，串联关键词消费、生成、质检、反馈和后处理。
- `core/prompt_optimizer.py`
  从文章和监测结果中提炼下一轮 Prompt 指导。
- `core/active_prober.py`
  对 AI 平台做主动探测，识别高引用信号。
- `core/feedback_store.py`
  保存探测结果和关键词级反馈摘要。
- `database/feedback_schema.sql`
  反馈与探测相关表结构。
- `backend/` 和 `frontend_v2/`
  API 与新控制台。

## 快速开始

下面这版按“第一次接触仓库的人也能照着跑”的思路写。推荐先把本地最小链路跑通，再决定是否切 Docker、静态站点或生产部署。

### 1. 准备环境

建议环境：

- Python 3.11+
- Node.js 20.19+
- MySQL 8
- 可选：Docker / Docker Compose

如果你只想先验证主流程，最低要求是：

- 一个可访问的 MySQL 实例
- 一个可用的 OpenAI 兼容 LLM 接口
- Python 运行环境

前端控制台和主动探测不是第一步必须跑通的部分。

### 2. 配置环境变量

```bash
cp .env.example .env
```

至少需要配置：

- `OPENAI_API_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

说明：

- 推荐优先使用 `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL`
- `DEEPSEEK_API_KEY` 只作为历史兼容回退变量保留
- 这不代表你必须使用某个指定供应商
- 只要你的模型服务提供 OpenAI 兼容接口，就可以接入

如果你想把它当成“某个组织/品牌/机构”的 GEO 引擎来使用，再配置：

- `TARGET_ENTITY_NAME`
- `TARGET_ENTITY_ALIASES`
- `TARGET_CAPABILITY_NOUN`

如果你想启用 AI 平台主动探测，再配置：

- `ENABLE_ACTIVE_PROBING=true`
- `ACTIVE_PROBE_PLATFORMS=kimi,doubao,deepseek`

如果你想本地跑前端，并且不是用默认地址，再额外配置：

- `frontend_v2/.env.local`
- `VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1`

### 3. 准备数据库

先创建数据库，例如：

```sql
CREATE DATABASE geo_engine CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

如果你沿用默认容器配置，也可以继续使用 `geo_knowledge_engine`，关键是与你的 `.env` 保持一致。

然后执行迁移：

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

如果你使用的是已有旧库，可以先阅读 [Backend Migrations](./docs/backend_migrations.md) 再决定是否 `upgrade head` 或 `stamp head`。

### 4. 启动依赖

如果用 Docker：

```bash
docker compose up -d mysql_db chromadb
```

如果你已经有外部 MySQL，而暂时不需要 ChromaDB，可以跳过这一步。

### 5. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6. 启动后端 API

```bash
uvicorn backend.app.main:app --reload --port 8001
```

启动后可以先检查：

```bash
curl http://127.0.0.1:8001/api/v1/health
curl http://127.0.0.1:8001/api/v1/system/status
```

如果第二个接口能返回数据库状态和 `llm_api_configured` 字段，说明最小链路已经通了。

### 7. 启动前端控制台

新控制台：

```bash
cd frontend_v2
npm install
npm run dev
```

默认开发地址通常是：

- 前端控制台：`http://127.0.0.1:5173`
- 后端 API：`http://127.0.0.1:8001/api/v1`

旧版 Streamlit 控制台如果还要用：

```bash
streamlit run dashboard/app.py --server.port 8503
```

### 8. 运行主流程

```bash
python batch_generator.py
```

这一步会消费关键词、生成文章、做质检，并在已启用时写入反馈信息。

### 9. 验证是否跑通

建议按这个顺序检查：

1. `health` 接口返回正常。
2. `system/status` 返回数据库状态正常，`llm_api_configured=true`。
3. `batch_generator.py` 启动后没有立刻因为数据库或密钥报错退出。
4. 后台能看到文章、关键词、运行或反馈数据开始变化。

### 10. 跑一条最小闭环 Demo

如果你不想先研究全部目录，直接跟着这条链路理解系统：

1. 配置 `.env`
2. 启动 MySQL / ChromaDB
3. 执行 Alembic 迁移
4. 启动 `uvicorn`
5. 启动 `frontend_v2`
6. 执行 `python batch_generator.py`
7. 在控制台查看系统状态、内容中心、运行中心和发布中心

对应的演示文档见 [最小闭环 Demo](./docs/minimal_demo.md)。

如果你想直接一键起演示环境：

```bash
cp .env.example .env
make demo
make demo-run
```

停止演示环境：

```bash
make demo-down
```

### 11. Docker 一键体验

```bash
docker compose up --build
```

适合第一次快速起全套依赖，但不建议直接把它当生产方案。

### 12. 直接拉取预构建镜像

如果你只是想先确认公开镜像可用，可以直接拉取：

```bash
docker pull ghcr.io/xxxbozzz/gitgeo:latest
```

如果你想固定到某次构建，也可以使用：

```bash
docker pull ghcr.io/xxxbozzz/gitgeo:sha-<commit>
```

说明：

- `latest` 对应默认分支上的最新成功镜像
- `sha-<commit>` 对应某次具体提交，适合回滚和固定部署

### 13. 使用预构建镜像启动

仓库里已经带了生产 compose 模板 [docker-compose.prod.yml](./docker-compose.prod.yml)。

最小示例：

```bash
export GEO_APP_IMAGE=ghcr.io/xxxbozzz/gitgeo:latest
docker compose -f docker-compose.prod.yml up -d
```

如果你只想先拉镜像验证，不一定要把整套服务都起起来。更完整的生产部署建议见 [docs/ops_deploy_runbook.md](./docs/ops_deploy_runbook.md)。

## 关键配置项

| 环境变量 | 说明 |
|---|---|
| `OPENAI_API_KEY` | 推荐使用的 LLM API Key 变量 |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址，例如你自己的网关或第三方代理 |
| `OPENAI_MODEL` | 默认模型名 |
| `DEEPSEEK_API_KEY` | 历史兼容回退变量，只有旧实现或旧部署脚本仍依赖时才需要 |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | 数据库连接 |
| `VITE_API_BASE_URL` | 前端开发环境下连接的后端 API 地址 |
| `VITE_OPEN_SOURCE_WATERMARK` | 前端控制台显示的开源署名水印 |
| `VITE_OPEN_SOURCE_WATERMARK_URL` | 开源署名跳转链接 |
| `TARGET_ENTITY_NAME` | 目标组织名，例如某品牌、机构、团队 |
| `TARGET_ENTITY_ALIASES` | 目标组织别名，逗号分隔 |
| `TARGET_CAPABILITY_NOUN` | 能力口径名称，例如“组织能力”“工程能力”“实施能力” |
| `ENABLE_ACTIVE_PROBING` | 是否启用 AI 平台主动探测 |
| `ACTIVE_PROBE_PLATFORMS` | 启用哪些平台探测 |

## 推荐部署路径

如果你不知道该选哪种方式，可以直接按下面判断：

- 只想本地验证功能：本地 Python + 本地或远程 MySQL
- 想给团队演示：`docker compose up`
- 想做公开知识站：GEO Engine 负责产出内容，站点层交给 Hugo / Docusaurus / MkDocs
- 想做稳定生产环境：后端、生成器、调度器拆成独立容器，通过 CI/CD 发布

## 已可用与路线图

### 当前已可用

- 本地或容器启动后端 API 与新控制台
- 跑通“生成 -> 评分 / 返修 -> 反馈 -> 发布记录”主链路
- 用 OpenAI 兼容接口驱动内容生成
- 在控制台查看文章、运行、系统状态和发布记录
- 通过渠道适配层手动触发发布

### 当前仍在演进

- 发布层从具体平台实现向通用 `channel adapter` 抽象迁移
- 发布页和接口已支持 `channel` 口径，但底层数据库字段仍兼容旧 `platform` 语义
- 一些历史变量和旧能力命名仍保留兼容层

### 路线图

- 根据行业与文章类型自动选择高权重渠道
- 将发布路由升级为“渠道画像 + 评分 + 适配器”的统一框架
- 把反馈结果回流到渠道权重，而不只是回流到 Prompt
- 继续剥离旧业务命名，形成更纯粹的通用开源内核

## 常见问题

### 1. 后端能启动，但返修或生成时报 LLM 未配置

检查这些变量里是否至少有一个可用：

- `OPENAI_API_KEY`

如果你还在兼容旧配置，也可以临时使用：

- `DEEPSEEK_API_KEY`

如果你使用自定义网关，还要检查：

- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

### 2. 数据库连接失败

优先检查：

- `DB_HOST` 是否与运行环境一致
- Docker 场景下是否应写成 `mysql_db`
- 本地直连场景下是否应写成 `127.0.0.1`
- 数据库名是否已经创建

### 3. 前端能打开，但系统页一直报错

先确认：

- 后端是否运行在 `8001`
- 前端请求的 API Base URL 是否正确
- `/api/v1/system/status` 是否可访问

### 4. 主流程没有产出新内容

先看：

- 是否有待消费关键词
- LLM Key 是否有效
- 数据库写权限是否正常
- 反馈链路是否把文章判成低质量后拦下了

## 开源边界

为了避免误解，这里明确说清楚当前仓库的边界：

- 这是一个已经能跑通主链路的开源系统骨架
- 这不是一个已经完成“智能选站自动发布”的成熟分发平台
- 当前最完整的能力在“生成、评分、反馈、Prompt 方法论”
- 当前最适合展示的能力是系统结构与闭环设计，而不是平台覆盖数量

## 官网同步与内容站发布

这个仓库不强制绑定某一种官网同步方式。更推荐把“生成引擎”和“站点部署”解耦。

### 方法 A：静态站点生成 + Git 驱动发布

适合：

- 文档中心
- 帮助中心
- 技术百科
- 开发者门户

推荐方案：

- [Hugo](https://github.com/gohugoio/hugo)
  2026-04-09 检查约 `87.5k` stars。适合内容站、博客、知识库，构建快。
- [Docusaurus](https://github.com/facebook/docusaurus)
  2026-04-09 检查约 `64.4k` stars。适合文档站、开发者门户、版本化内容。
- [docsify](https://github.com/docsifyjs/docsify)
  2026-04-09 检查约 `31.1k` stars。适合轻量 Markdown 驱动站点，无需复杂构建。
- [Material for MkDocs](https://github.com/squidfunk/mkdocs-material)
  2026-04-09 检查约 `26.5k` stars。适合结构清晰、搜索体验好的知识库。

推荐做法：

1. GEO Engine 只负责产出 Markdown / JSON / HTML。
2. 静态站点仓库负责模板、导航、SEO 和部署。
3. 用 GitHub Actions、Pages、Netlify 或你自己的 CI 做持续发布。

### 方法 B：输出静态文件后同步到自有服务器

适合：

- 已有官网
- 已有 CMS
- 已有 Nginx / CDN / 自建主机

推荐方案：

- [easingthemes/ssh-deploy](https://github.com/easingthemes/ssh-deploy)
  2026-04-09 检查约 `1.3k` stars。适合通过 rsync + SSH 把 `dist/` 或 HTML 输出同步到服务器。
- [Burnett01/rsync-deployments](https://github.com/Burnett01/rsync-deployments)
  2026-04-09 检查约 `433` stars。适合把构建产物从 GitHub Actions 直接同步到远端目录。

推荐做法：

1. 在 CI 中生成静态产物。
2. 通过 rsync over SSH 部署到目标目录。
3. 在远端做缓存刷新、软链接切换或 Nginx reload。

### 方法 C：直接使用 Git 托管平台的站点能力

适合：

- 开源文档
- API 说明
- 公共知识库

可选方式：

- GitHub Pages
- Netlify GitHub App

Netlify 的 GitHub App 支持“每次提交自动构建与部署”，也适合给文档站、营销站或知识站做预览环境。

## 多渠道发布建议

这个项目更推荐“发布适配器”模式，而不是把渠道写死在核心引擎里。

### 推荐架构

1. GEO Engine 产出标准化内容。
2. 统一的 `publication` 事件层负责把内容分发给不同渠道。
3. 每个渠道各自有 adapter，不要把站点逻辑塞回生成链路。

### 可以优先考虑的开源替代方案

- [n8n](https://github.com/n8n-io/n8n)
  2026-04-09 检查约 `183k` stars。适合把“生成完成 -> 审核 -> 发布 -> 回写状态”做成可视化工作流，连接 Slack、Discord、Telegram、Notion、Webhook、数据库等。
- [Crosspost](https://github.com/humanwhocodes/crosspost)
  2026-04-09 检查约 `537` stars。适合把同一条内容同步发到多个社交网络，目前支持 Bluesky、Mastodon、X/Twitter、LinkedIn、Discord、Telegram、Dev.to、Nostr 等。
- [RSSHub](https://github.com/DIYgod/RSSHub)
  2026-04-09 检查约 `43.3k` stars。适合把站点、频道或平台内容转换成标准 RSS，再交给聚合或自动化系统处理。
- [RSSHub Radar](https://github.com/DIYgod/RSSHub-Radar)
  2026-04-09 检查约 `7.1k` stars。适合发现站点已有 RSS 或 RSSHub 路由，方便做订阅分发链路。

### 推荐替代思路

- 网站与知识库：优先走静态站点发布
- 社交渠道：优先走 workflow / cross-posting
- 内部通知：优先走 webhook / Slack / 飞书 / Discord / Telegram
- 二次分发：优先走 RSS / webhook / automation，而不是把所有平台账号逻辑嵌进主代码库

## Prompt 指南

这个仓库保留两类 Prompt 文档，对应两种使用方式。

### 1. 给系统设计者

如果你想让系统按行业自动完成：

- 生文
- 监测
- 自迭代
- 评分
- 选择高权重网站
- 自动发布

请看：

- [自动化 Prompt 流水线指南](./docs/prompt_pipeline_guide.md)

### 2. 给创作者和内容策略人员

如果你想教创作者自己构建这一整套 Prompt 资产，请看：

- [创作者 Prompt 构建指南](./docs/prompt_creator_guide.md)

## 适合怎么用

- 如果你要做“企业知识站 + AI 引用优化”：直接用它做核心引擎
- 如果你要做“行业内容中台”：把它当作生成与反馈层
- 如果你要做“多平台分发”：把它和 n8n / RSSHub / 静态站点 CI 组合使用

## 参考链接

- [系统结构总览](./docs/system_structure.md)
- [AI 反馈闭环](./docs/ai_feedback_loop.md)
- [自动化 Prompt 流水线指南](./docs/prompt_pipeline_guide.md)
- [创作者 Prompt 构建指南](./docs/prompt_creator_guide.md)
- [最小闭环 Demo](./docs/minimal_demo.md)
- [英文首页](./README_EN.md)
- [贡献指南](./CONTRIBUTING.md)
- [前端需求草案](./docs/frontend_v2_requirements.md)
- [运行记录说明](./docs/geo_runtime_jobs.md)
- [LICENSE](./LICENSE)
