# CLAUDE.md System Prompt

## Rules

- Read `docs/architecture.md` for an architectural overview of the project. Refactors should always start here first.
- The project uses `uv`, `ruff` and `mypy`
- Run commands should be prefixed with `uv`: `uv run ...`
- Use `asyncio` features, if such is needed
- Absolutely no useless comments! Every class and method does not need to be documented (unless it is legitimetly complex or "lib-ish")
