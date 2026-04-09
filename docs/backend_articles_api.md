# Backend Articles API

## 目标

把旧 Dashboard 的“内容管理”和“最新入库记录”数据面收敛成稳定的只读接口。

## 当前接口

- `GET /api/v1/articles`
- `GET /api/v1/articles/summary`
- `GET /api/v1/articles/{article_id}`

## 查询能力

### `GET /api/v1/articles`

支持参数：

- `status=draft|approved|published`
- `min_score`
- `query`
- `limit`
- `offset`

返回：

- 分页文章列表
- 统一字段：`id / title / slug / quality_score / publish_status / dims / timestamps`

### `GET /api/v1/articles/summary`

返回：

- 文章总数
- 草稿数
- 已通过数
- 已发布数
- 平均质量分

### `GET /api/v1/articles/{article_id}`

返回：

- 基础文章字段
- `meta_json`
- `content_markdown`
- 绑定关键词
- 入站 / 出站内链数量
- 最近一次关联运行 ID 和状态

## 原则

- 仍然只做只读接口
- 详情接口直接为内容详情页和抽屉预览服务
- 前端不再自己拼关键词、链接和运行状态查询
