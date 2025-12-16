# Agent Chat CLI

This is the Python version of [agent-chat-cli](https://github.com/damassi/agent-chat-cli), which uses the [claude-agent-sdk](https://github.com/anthropics/claude-agent-sdk-python) under the hood. Terminal UI is built on top of the very impressive [Textual](https://textual.textualize.io/).

https://github.com/user-attachments/assets/865cfed5-7f6f-4db6-a5aa-ef2909eedbf6

## Why?

This tool is for those who want slightly more behavioral control over their MCP servers via configurable system prompts, and a minimal terminal-based MCP form factor for interaction.

Many different things are possible here thanks to the underlying Claude Agent SDK -- think of this as a light-weight `claude-code` -- but the main purpose, at least for me, is a simple and performant MCP interface to whatever tools I typically use day-to-day, something that lives outside of an editor or `claude` itself.

> **Note**: The Python/Textual version is visually sturdier than the Node.js/React Ink version. No more crazy Node.js terminal jank in long-running sessions!

## Setup

This app uses [uv](https://github.com/astral-sh/uv) for package management so first install that. Then:

```bash
git clone https://github.com/damassi/agent-chat-cli-python.git

# Install deps and setup .env
make install
```

Update the `.env` with your `ANTHROPIC_API_KEY` and then run:

```bash
make start

# Alternatively, if in dev (see below)
make dev
```

Additional MCP servers are configured in `agent-chat-cli.config.yaml` and prompts added within the `prompts` folder.

## Development

- Install pre-commit hooks via [pre-commit](https://pre-commit.com/)
  - `uv run pre-commit install`
- Type-checking is via [ty](https://github.com/astral-sh/ty):
  - `make type-check`
- Linting and formatting is via [Ruff](https://docs.astral.sh/ruff/)
  - `make lint`
- Testing is via [pytest](https://docs.pytest.org/):
  - `make test`

See [docs/architecture.md](docs/architecture.md) for an overview of the codebase structure.

### Textual Dev Console

Textual has an integrated logging console that one can boot separately from the app to receive logs.

In one terminal pane boot the console:

```bash
make console
```

> Note: this command intentionally filters out more verbose notifications. See the Makefile to configure.

And then, in a second terminal pane, start the textual dev server:

```bash
make dev
```
