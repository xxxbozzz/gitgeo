# gitgeo

> The first open-source **one-stop GEO (Generative Engine Optimization) engine**.
> Production → Scoring → Feedback → Distribution. All in one `docker compose up`.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/xxxbozzz/gitgeo?style=social)](https://github.com/xxxbozzz/gitgeo/stargazers)

> 🇬🇧 [English](README_EN.md) | 🇨🇳 简体中文 | 🇯🇵 日本語 (coming soon)

---

## What makes gitgeo different

Most content tools do three things: find keywords → generate articles → publish.

**gitgeo does the missing half:** it measures whether AI search engines actually cite your content, then feeds that data back into the next generation cycle.

| | Typical GEO tool | gitgeo |
|---|---|---|
| Content generation | ✅ | ✅ Multi-agent CrewAI pipeline |
| Quality scoring | ❌ | ✅ 9-dimension auto-scoring + auto-refix |
| AI visibility tracking | ❌ | ✅ Probes DeepSeek/Kimi/Doubao for brand mentions |
| Prompt feedback loop | ❌ | ✅ Citation signals → optimize next prompt |
| One-click deploy | ❌ | ✅ `docker compose up` |
| External publishing | ❌ | ✅ Zhihu/WeChat + extensible adapters |

---

## 5-minute quickstart

```bash
# 1. Clone and configure
git clone https://github.com/xxxbozzz/gitgeo.git && cd gitgeo
cp .env.example .env
# Edit .env: set GEO_LLM_API_KEY (everything else has sensible defaults)

# 2. Start
docker compose up -d

# 3. Verify
curl http://localhost:8001/api/v1/ready   # → {"status":"ok"}
open http://localhost:8503  # Dashboard
```

**That's it.** The init container creates all tables and seeds keywords automatically. The generator starts producing articles within seconds.

> Need more keywords? Edit `seed_topics.json` or add them via API:
> ```bash
> curl -X POST http://localhost:8001/api/v1/keywords \
>   -H "Content-Type: application/json" \
>   -d '{"keyword": "your topic here"}'
> ```

---

## Architecture

```
┌─────────────────────────────────────────┐
│           Vue 3 Console / Streamlit      │
│     Dashboard │ Articles │ Keywords      │
├─────────────────────────────────────────┤
│        FastAPI Backend (/api/v1)         │
├─────────────────────────────────────────┤
│              Core Engine                  │
│  ┌───────────┐ ┌─────────┐ ┌─────────┐ │
│  │ Generator │ │ Scorer  │ │ Prober  │ │
│  │ (CrewAI)  │ │(9-dim)  │ │(AI vis) │ │
│  └───────────┘ └─────────┘ └─────────┘ │
│  ┌───────────────────────────────────┐  │
│  │     Prompt Feedback Loop          │  │
│  │  probe → analyze → optimize → gen │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│       MySQL │ ChromaDB │ Docker         │
└─────────────────────────────────────────┘
```

### The feedback loop (gitgeo's core innovation)

```
1. Generate article with evidence (standards, docs, test data)
2. Auto-score across 9 quality dimensions
3. Probe AI platforms: "Does DeepSeek mention our brand for this keyword?"
4. Write probe results as structured feedback
5. Inject feedback into the next generation prompt
6. Each cycle produces more citable content
```

---

## Key features

- **Multi-agent content generation** — Collector → Structurer → Writer → Publisher, CrewAI orchestrated
- **9-dimension quality scoring** — Length, structure, tables, FAQ, references, definitions, banned words, logic chains, title quality. Auto-refix up to 3 attempts.
- **Active AI probing** — Check if DeepSeek, Kimi, and Doubao mention your brand for target keywords
- **Capability memory** — Verified organizational capabilities as queryable facts for agents
- **Prompt optimization** — Citation signal analysis → keyword variants → prompt guidance
- **Multi-platform publishing** — Zhihu, WeChat, plus extensible adapters
- **Modern API + Console** — FastAPI backend + Vue 3 dashboard
- **Docker-native** — One `docker compose up` starts everything

---

## Configuration

All in `.env`. The only required field is an LLM API key:

```bash
GEO_LLM_API_KEY=sk-your-key
GEO_LLM_BASE_URL=https://api.deepseek.com   # Any OpenAI-compatible API
GEO_LLM_MODEL=deepseek-chat
```

Works with DeepSeek, OpenAI, Groq, local vLLM, or any OpenAI-compatible endpoint.

---

## Documentation

- [System Architecture](docs/system_structure.md)
- [AI Feedback Loop](docs/ai_feedback_loop.md)
- [Prompt Pipeline Guide](docs/prompt_pipeline_guide.md)
- [Creator Guide](docs/prompt_creator_guide.md)
- [Minimal Demo](docs/minimal_demo.md)

---

## License

MIT © [xxxbozzz](https://github.com/xxxbozzz)
