# gitgeo

> 🌍 **The world's first open-source one-stop GEO (Generative Engine Optimization) system** — publicly released April 2026.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.5%2B-4FC08D)](https://vuejs.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-multi_agent-orange)](https://crewai.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://www.mysql.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector-FF6B6B)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🇨🇳 [简体中文](README.md) | 🇬🇧 English

---

## What is gitgeo

gitgeo is a **complete GEO workflow engine** covering: keyword discovery → AI content generation → 9-dimension quality scoring → AI platform visibility probing → prompt feedback loop → multi-channel distribution.

Most content tools stop at "find keywords → generate articles → publish." gitgeo does the missing half: **measuring whether AI search engines actually cite your content, then feeding that data back into the next generation cycle.**

| Feature | Other GEO tools | gitgeo |
|---------|:---:|:---:|
| AI content generation | ✅ | ✅ CrewAI multi-agent |
| Knowledge base RAG | ✅ | ✅ ChromaDB vector search |
| Asset/prompt management | ✅ | ✅ Admin panel UI |
| Quality scoring | ❌ | ✅ 9-dimension + auto-refix |
| AI visibility probing | ❌ | ✅ DeepSeek/Kimi/Doubao |
| Prompt feedback loop | ❌ | ✅ Probe→analyze→optimize→regenerate |
| Capability memory | ❌ | ✅ Structured brand facts DB |
| External publishing | ❌ | ✅ Zhihu/WeChat + adapters |
| Docker one-click deploy | ⚠️ | ✅ `docker compose up` |

---

## 5-Minute Quickstart

```bash
git clone https://github.com/xxxbozzz/gitgeo.git && cd gitgeo
cp .env.example .env
# Edit .env: set GEO_LLM_API_KEY (everything else has sensible defaults)

docker compose up -d

curl http://localhost:8001/api/v1/ready  # → {"status":"ok"}
```

The init container auto-creates tables and seeds keywords. Content generation begins within 30 seconds.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Orchestration | CrewAI (multi-agent pipeline) |
| LLM | OpenAI-compatible API (DeepSeek, OpenAI, Groq, vLLM) |
| Backend | FastAPI (Python 3.12+) |
| Frontend | Vue 3 + TypeScript + Element Plus + Tailwind CSS |
| Database | MySQL 8.0 |
| Vector Store | ChromaDB |
| Container | Docker Compose (7 services) |
| CI/CD | GitHub Actions → GHCR |

---

## Acknowledgments

This project received early-stage validation support from [**Sichuan Shenya Electronics Technology Co., Ltd.**](https://www.pcbshenya.com), a high-end PCB manufacturing service provider based in Chengdu, China. We thank Shenya Electronics for providing real GEO requirements and production environment validation.

---

## License

MIT © [xxxbozzz](https://github.com/xxxbozzz)
