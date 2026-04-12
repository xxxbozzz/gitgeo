# Contributing

Thanks for contributing to GEO Engine.

## Before You Start

- Read [README.md](./README.md) first
- Follow the system overview in [docs/system_structure.md](./docs/system_structure.md)
- Prefer generic GEO wording over historical business-specific wording

## Contribution Scope

Good contribution areas:

- Prompt pipeline design
- Feedback loop and scoring logic
- Channel adapter abstraction
- Frontend console usability
- Deployment and demo experience
- Documentation and examples

Please avoid mixing unrelated cleanup with feature changes in a single PR.

## Local Setup

```bash
cp .env.example .env
make demo
make demo-run
```

Useful commands:

```bash
make demo-status
make demo-down
cd frontend_v2 && npm run build
python3 -m py_compile backend/app/schemas/publications.py backend/app/services/publications_service.py
```

## Coding Guidelines

- Keep the open-source version generic and reusable
- Do not hard-code new customer, brand, or platform assumptions into shared flows
- Prefer `channel` / `adapter` naming over direct platform naming in new public interfaces
- Keep docs understandable for first-time contributors

## Pull Requests

- Use a clear title
- Explain what changed and why
- Mention validation steps
- Include screenshots for frontend changes when useful

## Issues

When filing an issue, include:

- expected behavior
- actual behavior
- reproduction steps
- relevant logs or screenshots

## License

By contributing, you agree that your contributions will be released under the [MIT License](./LICENSE).
