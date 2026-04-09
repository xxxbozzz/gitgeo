# GEO 前端 V2 需求说明

## 1. 目标

前端 V2 不是单纯把现有 Streamlit 换成一个新壳，而是要把 GEO 系统做成工程化中控台。

前端需要承接 3 类职责：

- 展示系统运行和产出状态
- 承接文章、发布、运行等高频操作
- 为后续关键词中心、能力库、知识图谱、告警系统预留稳定扩展位

## 2. 推荐技术栈

### 核心栈

- Vue 3
- Vite
- Vue Router
- Pinia
- Element Plus
- Apache ECharts
- Axios
- `@tanstack/vue-query`

### 选择要求

- 必须使用组件化和模块化目录，不允许把页面、接口、状态、表单逻辑揉成单文件
- 必须有统一 API 层，不允许页面直接拼接 `fetch`
- 必须有统一错误处理、统一 loading 态、统一空态组件
- 必须支持桌面端优先，同时保证移动端可读

## 3. 视觉与交互要求

### 风格

- 走工业控制台风格，不走炫技大屏风格
- 主色建议：深蓝、冷灰、少量青色高亮
- 强调数据表格、状态标签、抽屉详情、卡片分区
- 图表信息优先，弱化装饰性阴影和发光

### 交互规则

- 读页面使用局部轮询，不允许整页刷新
- 写操作必须有确认弹窗
- 写操作成功后只刷新相关查询，不做全页 reload
- 页面必须统一处理 `loading / empty / error / success` 四态
- 错误提示统一 toast + 错误面板

## 4. 前端目录建议

建议前端目录新建为 `dashboard-v2/`，最少包含：

- `src/app`
- `src/router`
- `src/layouts`
- `src/pages`
- `src/components`
- `src/modules/articles`
- `src/modules/runs`
- `src/modules/publications`
- `src/modules/system`
- `src/api`
- `src/stores`
- `src/composables`
- `src/types`
- `src/styles`

## 5. 页面与功能要求

### 5.1 总览

目标：

- 让管理者快速看懂今天系统有没有正常产出

首版必须实现：

- KPI 卡片
- 最近 7 日产出趋势
- 待处理关键词
- 最新文章
- 草稿 / 已通过文章看板

二期预留：

- 最新运行状态
- 最新发布结果
- 最新告警

### 5.2 运行中心

目标：

- 替代纯日志式排查

必须实现：

- 运行列表
- 状态筛选
- 触发方式筛选
- 关键词搜索
- 运行详情
- 步骤时间线
- 失败信息展示

预留：

- 重试入口

### 5.3 内容中心

目标：

- 集中管理文章资产

必须实现：

- 文章列表
- 状态筛选
- 最低分筛选
- 标题/slug 搜索
- 文章详情抽屉或详情页
- Markdown 正文展示
- 关键词展示
- 关联运行展示
- 手动返修
- 回收
- 手动发布

预留：

- 质量报告页
- 返修历史
- 导出记录
- 能力引用明细

### 5.4 发布中心

目标：

- 从“文章是否已发布”升级为“每个渠道发布是否成功”

必须实现：

- 发布记录列表
- 渠道筛选
- 状态筛选
- 触发方式筛选
- 文章搜索
- 发布详情
- 错误信息展示
- 重试入口

### 5.5 系统状态

目标：

- 把基本运维状态可视化

首版必须实现：

- 当前环境
- debug 状态
- 数据库状态
- LLM API 是否配置
- 当前 build 版本

预留：

- budget / token
- scheduler 状态
- 发布器状态
- 容器状态

### 5.6 关键词中心

当前为预留模块，前端先保留菜单和路由占位。

后续需要承接：

- 关键词池
- 真空词池
- 已消费 / 待消费 / 失败重试
- 技术集群分布

### 5.7 能力库中心

当前为预留模块，前端先保留菜单和路由占位。

后续需要承接：

- 能力项列表
- 来源列表
- 启用 / 停用
- 修订记录
- 最近引用文章

### 5.8 知识图谱

当前为预留模块，前端先保留菜单和路由占位。

后续需要承接：

- 技术集群图
- 文章与能力项关联图
- 内链网络图

## 6. 当前真实可对接 API

后端 API 前缀固定为：

- `/api/v1`

统一返回结构为：

```json
{
  "success": true,
  "message": "string",
  "data": {},
  "error_code": null
}
```

前端必须统一消费这个 envelope，不要假设接口直接返回业务对象。

### 6.1 Overview

- `GET /api/v1/overview/kpis`
- `GET /api/v1/overview/trend?days=7`
- `GET /api/v1/overview/board?pending_limit=5&article_limit=5`
- `GET /api/v1/overview/latest-articles?limit=8`

主要字段：

- `kpis`: `articles_total` `passed_articles` `pending_keywords` `average_quality_score` `internal_links` `latest_article_at`
- `trend.items[]`: `day` `count`
- `board.pending_keywords[]`: `id` `keyword` `search_volume` `difficulty`
- `board.draft_articles[]` / `ready_articles[]`: 文章摘要对象

### 6.2 Articles

- `GET /api/v1/articles`
- `GET /api/v1/articles/summary`
- `GET /api/v1/articles/{article_id}`
- `POST /api/v1/articles/{article_id}/refix`
- `POST /api/v1/articles/{article_id}/recycle`
- `POST /api/v1/articles/{article_id}/publish`

查询参数：

- `status`
- `min_score`
- `query`
- `limit`
- `offset`

详情字段重点：

- `meta_json`
- `content_markdown`
- `target_keywords`
- `outgoing_links_count`
- `incoming_links_count`
- `related_run_id`
- `related_run_status`

发布请求体：

```json
{
  "channels": ["longform_channel", "mobile_channel"],
  "go_live": false
}
```

### 6.3 Runs

- `GET /api/v1/runs`
- `GET /api/v1/runs/summary`
- `GET /api/v1/runs/recent-failures`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/steps`

查询参数：

- `status`
- `trigger_mode`
- `keyword`
- `limit`
- `offset`

列表字段重点：

- `run_uid`
- `run_type`
- `trigger_mode`
- `keyword`
- `article_id`
- `status`
- `current_step`
- `retry_count`
- `error_message`

步骤字段重点：

- `step_code`
- `step_name`
- `attempt_no`
- `status`
- `error_message`
- `detail_json`

### 6.4 Publications

- `GET /api/v1/publications`
- `GET /api/v1/publications/{publication_id}`
- `POST /api/v1/publications/{publication_id}/retry`

查询参数：

- `article_id`
- `channel`
- `status`
- `trigger_mode`
- `query`
- `limit`
- `offset`

列表字段重点：

- `article_title`
- `channel_key`
- `channel_label`
- `adapter_key`
- `adapter_label`
- `publish_mode`
- `status`
- `trigger_mode`
- `attempt_no`
- `retryable`
- `external_url`
- `message`
- `error_message`
- `published_at`

详情额外字段：

- `request_payload_json`
- `response_payload_json`
- `retry_attempts_total`

### 6.5 System

- `GET /api/v1/system/status`

当前字段：

- `environment`
- `debug`
- `database`
- `llm_api_configured`
- `build`

## 7. 前端需要预留但后端暂未完成的接口

这些接口在方案里已经被定义，但当前后端还没有全部完成，前端需要提前按模块预留页面、类型和数据访问层。

### 7.1 Overview 预留

- `GET /api/v1/overview/latest-runs`
- `GET /api/v1/overview/alerts`

### 7.2 Runs 预留

- `POST /api/v1/runs/{run_id}/retry`

### 7.3 Articles 预留

- `GET /api/v1/articles/{article_id}/quality`

### 7.4 Keywords 预留

- `GET /api/v1/keywords`
- `GET /api/v1/gap-keywords`
- `GET /api/v1/keywords/clusters`

### 7.5 Capabilities 预留

- `GET /api/v1/capabilities`
- `GET /api/v1/capabilities/{spec_id}`
- `GET /api/v1/capabilities/{spec_id}/sources`
- `POST /api/v1/capabilities/{spec_id}/disable`

### 7.6 System 预留

- `GET /api/v1/system/build`
- `GET /api/v1/system/budget`

## 8. 前端数据层要求

### Query 规范

- 所有只读接口统一走 Vue Query
- 列表页 query key 必须包含筛选参数
- 写操作成功后只 `invalidate` 关联 key

建议 query key：

- `['overview', 'kpis']`
- `['overview', 'trend', days]`
- `['overview', 'board', pendingLimit, articleLimit]`
- `['articles', filters]`
- `['article', articleId]`
- `['runs', filters]`
- `['run', runId]`
- `['run-steps', runId]`
- `['publications', filters]`
- `['publication', publicationId]`
- `['system', 'status']`

### API 层规范

- 统一 Axios 实例
- 统一读取 `VITE_API_BASE_URL`
- 默认前缀建议：`/api/v1`
- 统一响应解包 `success/message/data/error_code`
- 统一 4xx/5xx 拦截

## 9. 环境变量要求

前端至少预留：

```bash
VITE_API_BASE_URL=http://localhost:8001/api/v1
```

生产中如果前后端同域反代，可改为：

```bash
VITE_API_BASE_URL=/api/v1
```

## 10. 路由建议

- `/overview`
- `/runs`
- `/articles`
- `/articles/:id`
- `/publications`
- `/publications/:id`
- `/system`
- `/keywords`
- `/capabilities`
- `/graph`

## 11. 第一阶段交付范围

如果前端现在就开工，建议首批只做：

1. 总览
2. 运行中心
3. 内容中心
4. 发布中心
5. 系统状态

先不要做：

- 复杂认证
- 知识图谱高级交互
- 能力库全量治理
- 真空词中心复杂运营能力

## 12. 结论

前端 V2 要用 Vue 3 管理台栈，把当前已经存在的 `overview / articles / runs / publications / system` 五组 API 承接起来，同时提前为 `keywords / capabilities / alerts / budget / retry` 等后续能力预留数据层和路由结构。这样才能保证这套前端不是一次性页面，而是 GEO 系统的长期中控层。
