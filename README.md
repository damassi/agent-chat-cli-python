# Agent Chat CLI

This is a less feature-rich Python version of [agent-chat-cli](https://github.com/damassi/agent-chat-cli), which uses the [claude-agent-sdk](https://github.com/anthropics/claude-agent-sdk-python) under the hood. Terminal UI is built on top of the very impressive [Textual](https://textual.textualize.io/).

https://github.com/user-attachments/assets/66a1d462-e51a-419f-80f3-fa69ee60db9c

## Purpose

This tool is for those who wish for slightly more control over their MCP servers via configurable system prompts, and a minimal terminal-based MCP form factor. (It can do a lot of things thanks to the Claude Agent SDK, but the main purpose, at least for me, is a simple, humble and performant MCP interface to whatever tools I typically use day-to-day.)

> Note: The Python version is visually sturdier than the Node.js version. No more crazy terminal flashing like in claude-code!

## Setup

This app uses [uv](https://github.com/astral-sh/uv) for package management so first install that. Then:

- `git clone https://github.com/damassi/agent-chat-cli-python.git`
- `uv sync`
- `uv run chat`

Additional MCP servers are configured in `agent-chat-cli.config.yaml` and prompts added within the `prompts` folder.
