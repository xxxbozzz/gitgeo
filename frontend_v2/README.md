# GEO Console V2

`frontend_v2` 是 GEO 系统的新控制台前端，基于 `Vue 3 + Vite + Vue Router + Pinia + Vue Query + Element Plus`。

## 本地开发

```bash
npm install
npm run dev
```

建议使用 `Node.js 20.19+`，避免依赖的 engine 要求与本地环境不匹配。

默认通过 `VITE_API_BASE_URL` 对接后端；未配置时，开发环境回退到 `http://localhost:8001/api/v1`。

如果你想改控制台底部的开源署名水印，可以配置：

- `VITE_OPEN_SOURCE_WATERMARK`
- `VITE_OPEN_SOURCE_WATERMARK_URL`

## 生产构建

```bash
npm run build
```

生产构建产物会在镜像构建阶段被复制到 `/app/frontend_v2_dist`，并由 FastAPI 在 `/console` 路径下提供静态访问：

- `http://<server>:8001/console`

## 当前模块

- 总览
- 运行中心
- 内容中心
- 发布中心
- 系统状态
- 关键词中心
- 能力库中心
- 知识图谱
