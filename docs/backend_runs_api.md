# Backend Runs API

## 目标

把 GEO 主流程里的 `geo_job_runs / geo_job_steps` 变成前端可以直接消费的只读接口。

## 当前接口

- `GET /api/v1/runs`
- `GET /api/v1/runs/summary`
- `GET /api/v1/runs/recent-failures`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/steps`

## 查询能力

### `GET /api/v1/runs`

支持参数：

- `status`
- `trigger_mode`
- `keyword`
- `limit`
- `offset`

返回：

- `items`
- `total`
- `limit`
- `offset`
- `warning`

### `GET /api/v1/runs/summary`

返回：

- `total_runs`
- `running_runs`
- `succeeded_runs`
- `failed_runs`
- `partial_runs`
- `latest_run_at`

### `GET /api/v1/runs/recent-failures`

返回最近失败或部分成功的运行记录，适合总览页失败面板。

### `GET /api/v1/runs/{run_id}`

返回单次运行摘要和步骤统计。

### `GET /api/v1/runs/{run_id}/steps`

返回该次运行的步骤时间线，适合运行详情页。

## 设计原则

- 所有接口都做降级处理，数据库不可用时返回空数据和 `warning`
- API 不直接暴露数据库原始 JSON 字符串，而是统一解码
- 这一步只做只读接口，不开放重试、终止、修改

## 下一步

前端 V2 可以先用这组接口做：

1. 运行中心列表页
2. 运行详情抽屉
3. 总览页最近失败运行面板
