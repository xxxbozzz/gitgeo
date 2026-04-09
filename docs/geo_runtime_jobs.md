# GEO 运行记录层

这份设计对应 GEO 工程化的第一步：把“日志里的流程”变成“数据库里的状态”。

新增资产：

- `database/job_runtime_schema.sql`
- `core/job_store.py`

## 目标

让系统能回答这几类问题：

- 这篇文章现在卡在哪一步
- 上一次失败是生成失败、质检失败、返修失败、导出失败还是内链失败
- 一个关键词对应的文章 run 是成功、失败还是部分成功
- 这次 run 一共返修了几次

## 表结构

### `geo_job_runs`

记录单次关键词处理的整体 run。

核心字段：

- `run_uid`：一次运行的唯一标识
- `keyword_id` / `keyword`
- `article_id`
- `status`：`running / succeeded / failed / partial`
- `current_step`
- `retry_count`
- `error_message`
- `detail_json`

### `geo_job_steps`

记录 run 里的具体步骤。

当前已接入的步骤：

- `generate`
- `quality_check`
- `repair`
- `export_html`
- `auto_link`
- `bind_keyword`

每个步骤都带：

- `attempt_no`
- `status`
- `error_message`
- `detail_json`
- `started_at / finished_at`

## 当前接入范围

在 `batch_generator.py` 里，单个关键词处理已经会：

1. 创建一条 `geo_job_runs`
2. 记录生成阶段
3. 记录每次质检
4. 记录每次返修
5. 记录导出 HTML
6. 记录自动内链
7. 记录关键词绑定
8. 在结束时写回 run 总状态

## 当前状态语义

- `succeeded`
  文章生成成功，质检通过，后处理也成功。
- `failed`
  生成失败或质检最终未通过。
- `partial`
  文章生成并通过质检，但导出、内链、关键词绑定里至少有一步失败。

## 下一步怎么接 Dashboard

推荐先加两个看板块：

1. 最近失败 run
   展示 `keyword / current_step / error_message / started_at`

2. 最近运行步骤
   展示 `run_uid / step_code / status / attempt_no / finished_at`

这样你后面就能从“看日志”升级成“看运行状态”。
