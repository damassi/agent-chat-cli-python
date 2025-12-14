# CLAUDE.md System Prompt

## Rules

- Read `docs/architecture.md` for an architectural overview of the project. Refactors should always start here first.
- The project uses `uv`, `ruff` and `mypy`
- Run commands should be prefixed with `uv`: `uv run ...`
- Use `asyncio` features, if such is needed
- Prefer early returns
- Absolutely no useless comments! Every class and method does not need to be documented (unless it is legitimetly complex or "lib-ish")
- Imports belong at the top of files, not inside functions (unless needed to avoid circular imports)

## Testing Rules

- **Never delete behavior tests to make things pass.** Fix the code or update the tests to reflect new behavior
