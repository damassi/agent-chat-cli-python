# Agent Chat CLI

This is a less feature-rich Python version of [agent-chat-cli](https://github.com/damassi/agent-chat-cli), which uses the [claude-agent-sdk](https://github.com/anthropics/claude-agent-sdk-python) under the hood. Terminal UI is built on top of the very impressive [Textual](https://textual.textualize.io/).

https://github.com/user-attachments/assets/66a1d462-e51a-419f-80f3-fa69ee60db9c

## Why?

This tool is for those who want slightly more control over their MCP servers via configurable system prompts, and a minimal terminal-based MCP form factor for interaction. Many more things are possible thanks to the Claude Agent SDK, but the main purpose, at least for me, is a simple, humble and performant MCP interface to whatever tools I typically use day-to-day.

> Note: The Python version is visually sturdier than the Node.js version. No more crazy terminal flashing like in Claude Code!

## Setup

This app uses [uv](https://github.com/astral-sh/uv) for package management so first install that. Then:

```bash
git clone https://github.com/damassi/agent-chat-cli-python.git

# Install deps and setup .env
make install
```

Update the `.env` with your `ANTHROPIC_API_KEY` and then run:

```bash
make chat

# Alternatively, if in dev (see below)
make dev
```

Additional MCP servers are configured in `agent-chat-cli.config.yaml` and prompts added within the `prompts` folder. By default, MCP servers are loaded dynamically via inference; set `mcp_server_inference: false` to load all servers at startup.

## Development

- Install pre-commit hooks via [pre-commit](https://pre-commit.com/)
  - `uv run pre-commit install`
- Typechecking is via [MyPy](https://github.com/python/mypy):
  - `uv run mypy src`
- Linting and formatting is via [Ruff](https://docs.astral.sh/ruff/)
  - `uv run ruff check src`

Textual has an integrated logging console which one can boot separately from the app to receive logs.

In one terminal pane boot the console:

```bash
make console
```

> Note: this command intentionally filters out more verbose notifications. See the Makefile to configure.

And then, in a second terminal pane, start the textual dev server:

```bash
make dev
```
