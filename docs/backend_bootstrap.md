# Backend Bootstrap

## 本次范围

这一步只做后端地基，不迁移旧逻辑，不改旧 Dashboard，不引入复杂 ORM。

已建立：

- `backend/app/main.py` FastAPI 统一入口
- `backend/app/core/settings.py` 强类型配置
- `backend/app/db/mysql.py` 轻量数据库访问层
- `backend/app/api/router.py` 路由总入口
- `backend/app/api/routes/health.py` 健康检查
- `backend/app/api/routes/overview.py` 总览 KPI
- `backend/app/api/routes/system.py` 系统状态
- `backend/app/schemas/api.py` 统一响应格式

## 统一约定

- API 前缀统一为 `/api/v1`
- 响应格式统一为 `success / message / data / error_code`
- 路由只做输入输出，不直接写 SQL
- SQL 读取统一通过 `services -> db` 层
- 当前阶段只做只读接口，写操作后移

## 启动方式

依赖安装完成后，可从仓库根目录启动：

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

容器化部署已约定通过 `docker-compose.yml` 中的 `backend` 服务启动，对外端口为 `8001`。

## 当前可用接口

- `GET /`
- `GET /api/v1/health`
- `GET /api/v1/ready`
- `GET /api/v1/overview/kpis`
- `GET /api/v1/overview/trend`
- `GET /api/v1/overview/board`
- `GET /api/v1/overview/latest-articles`
- `GET /api/v1/articles`
- `GET /api/v1/articles/summary`
- `GET /api/v1/articles/{article_id}`
- `GET /api/v1/runs`
- `GET /api/v1/runs/summary`
- `GET /api/v1/runs/recent-failures`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/steps`
- `GET /api/v1/system/status`

## 下一步

下一项建议直接做：

1. 把 `geo_job_runs / geo_job_steps` 写入链路和迁移链路彻底收口
2. 前端 V2 先接总览页和运行中心
3. 再迁移文章和发布相关 API
