# Backend Overview API

## 目标

为 Dashboard V2 的总览页提供完整数据面，不再让前端重复拼接多个散查询。

## 当前接口

- `GET /api/v1/overview/kpis`
- `GET /api/v1/overview/trend`
- `GET /api/v1/overview/board`
- `GET /api/v1/overview/latest-articles`

## 数据内容

### `kpis`

- 文章总数
- 质检通过数
- 待处理关键词数
- 平均质量分
- 内链总数
- 最新入库时间

### `trend`

- 最近 N 天的文章产出趋势

### `board`

- 待处理关键词列
- 草稿 / 待修复列
- 最新已入库文章列

### `latest-articles`

- 最新文章卡片列表

## 原则

- 由后端统一聚合总览页数据
- 前端只负责展示，不再复制旧 Streamlit 的 SQL 逻辑
- 数据库异常时返回空数据和 `warning`
