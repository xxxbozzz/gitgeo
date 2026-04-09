# Backend Migrations

## 目标

从这一步开始，数据库变更不再只靠手工执行 `.sql` 文件，而是统一纳入 Alembic。

## 本次策略

这次不是回头重写整个历史，而是建立一个 `baseline`：

- 把当前项目已经使用的核心 schema 收编进迁移系统
- 对已有线上库保持非破坏性
- 后续新增表、字段、索引都从这个 baseline 往后追加

## 当前 baseline 覆盖

- `geo_articles`
- `geo_keywords`
- `geo_links`
- `geo_capability_profiles`
- `geo_capability_sources`
- `geo_capability_specs`
- `geo_capability_spec_sources`
- `geo_job_runs`
- `geo_job_steps`

## 后续 revision

- `20260311_103000_add_article_publications`
  - 新增 `article_publications`
  - 用于平台级发布审计、失败追踪和重试链路

## 目录

- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/versions/20260310_213115_baseline_existing_schema.py`
- `backend/migrations/versions/20260311_103000_add_article_publications.py`

## 使用方式

先安装依赖：

```bash
venv/bin/pip install -r requirements.txt
```

查看迁移历史：

```bash
venv/bin/alembic -c backend/alembic.ini history
```

新环境建库：

```bash
venv/bin/alembic -c backend/alembic.ini upgrade head
```

已有生产库纳管：

```bash
venv/bin/alembic -c backend/alembic.ini stamp head
```

## 原则

- 生产环境已有表时，优先 `stamp head`
- 新环境需要完整建表时，使用 `upgrade head`
- baseline 不提供 destructive downgrade，避免误删生产数据

## 下一步

下一次数据库结构变更开始，统一新增 Alembic revision，不再只加新的 `.sql` 文件。
