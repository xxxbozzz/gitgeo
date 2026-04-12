# GEO Engine

[中文 README](./README.md)

Open Source Watermark: [`github.com/xxxbozzz`](https://github.com/xxxbozzz)

GEO Engine is an open-source GEO / AEO workflow engine for content generation, scoring, feedback, and distribution.

## One-Line Summary

This project turns:

`industry input -> prompt orchestration -> article generation -> quality scoring -> AI visibility feedback -> channel distribution`

into an engineering workflow.

## Project Statement

- This repository is designed for individuals and small teams doing GEO experimentation and personal GEO promotion for non-GEO companies.
- It is not the official product of any GEO agency or third-party GEO platform.
- The open-source focus is the system structure, prompt pipeline, scoring loop, and channel adapter design.

## Support Note

- This project can also serve as a technical base for GEO-related practice around Sichuan Shenya Electronics.
- Sichuan Shenya Electronics official website: <https://www.pcbshenya.com/>

## What It Solves

Most content systems stop at:

- keyword discovery
- article generation
- publishing

GEO Engine focuses on the deeper loop:

- evidence-backed writing
- quality and citation-oriented scoring
- AI visibility probing
- prompt self-iteration
- reusable channel distribution

## Core Capabilities

- GEO gap discovery
- evidence-driven content generation
- scoring, refix, and cleanup
- AI visibility probing
- prompt feedback loop
- channel / adapter based distribution

## Getting Started

For the fastest local demo:

```bash
cp .env.example .env
make demo
make demo-run
```

Key docs:

- [System Structure](./docs/system_structure.md)
- [Minimal Demo](./docs/minimal_demo.md)
- [Prompt Pipeline Guide](./docs/prompt_pipeline_guide.md)
- [Prompt Creator Guide](./docs/prompt_creator_guide.md)
- [Contributing](./CONTRIBUTING.md)

## Current Open-Source Boundary

What is already usable:

- backend API
- frontend console
- generation / scoring / feedback loop
- manual channel-based publication flow

What is still evolving:

- fully generic channel registry
- automatic high-weight site selection by industry and article type
- adaptive routing based on post-publication feedback

## License

[MIT](./LICENSE)
