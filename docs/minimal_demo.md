# 最小闭环 Demo

这份 Demo 面向第一次接触仓库的人，目标不是跑出完整生产系统，而是用一条最短链路理解 GEO Engine 的工作方式。

如果你想直接一键起本地演示环境，也可以用：

```bash
cp .env.example .env
make demo
```

这会自动完成：

- 启动 `mysql_db` 和 `chromadb`
- 准备 Python 虚拟环境
- 安装依赖
- 执行 Alembic 迁移
- 启动后端 API
- 启动前端控制台

然后再执行：

```bash
make demo-run
```

停止环境：

```bash
make demo-down
```

## 目标

你应该能看到这 4 个结果：

1. 后端健康检查通过
2. 系统状态页能确认数据库和 LLM 已配置
3. 主生成流程可以启动
4. 前端能看到文章、运行或发布相关数据入口

## 场景设定

这里用“行业 + 文章类型”的最小输入来理解系统：

- 行业：`industrial_iot`
- 文章类型：`guide`
- 目标：生成一篇带证据结构的行业指南文章，并进入后续评分 / 发布链路

这不是“自动选择高权重网站”的完成版演示。当前开源仓库重点是把生成、评分、反馈、发布适配层的骨架跑通。

## 1. 准备环境

```bash
cp .env.example .env
```

至少填这几项：

- `OPENAI_API_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

如果你本地跑前端，建议再确认：

- `frontend_v2/.env.local` 中的 `VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1`
- Node 版本至少为 `20.19+`

## 2. 启动数据库与后端

如果你使用仓库默认依赖：

```bash
docker compose up -d mysql_db chromadb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m alembic -c backend/alembic.ini upgrade head
uvicorn backend.app.main:app --reload --port 8001
```

验证：

```bash
curl http://127.0.0.1:8001/api/v1/health
curl http://127.0.0.1:8001/api/v1/system/status
```

## 3. 启动前端控制台

```bash
cd frontend_v2
npm install
npm run dev
```

默认访问：

- 前端：`http://127.0.0.1:5173`
- API：`http://127.0.0.1:8001/api/v1`

## 4. 跑主流程

回到仓库根目录：

```bash
python batch_generator.py
```

你不需要先理解所有 Prompt。先关注这条顺序：

1. 关键词进入消费链路
2. Prompt 被组装
3. 文章被生成
4. 系统做质量检查 / 返修
5. 结果进入控制台和后续反馈层

## 5. 在控制台里看什么

优先看这几个页面：

1. 系统状态页  
   确认 `llm_api_configured` 与数据库状态正常
2. 内容中心  
   看是否出现新文章、分数、正文和关联运行
3. 运行中心  
   看生成链路是否完成、失败在哪一步
4. 发布中心  
   看文章是否进入渠道发布记录

## 6. 这条 Demo 实际验证了什么

它验证的是：

- 这是一个“生成 + 评分 + 反馈 + 发布适配”的系统骨架
- Prompt 不是单点调用，而是流程中的多个环节
- 发布层已经具备“渠道 / 适配器”抽象方向

它还没有完整验证：

- 根据行业与文章类型自动选择高权重网站
- 基于真实发布效果自动调权
- 多站点智能路由

这些能力属于后续路线图。
