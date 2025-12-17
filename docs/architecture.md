# Architecture

Agent Chat CLI is a terminal-based chat interface for interacting with Claude agents, built with [Textual](https://textual.textualize.io/) and the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk).

### Directory Structure

```
src/agent_chat_cli/
├── app.py                     # Main Textual application entry point
├── core/
│   ├── actions.py             # User action handlers
│   ├── agent_loop.py          # Claude Agent SDK client wrapper
│   ├── renderer.py              # Message routing from agent to UI
│   ├── ui_state.py            # Centralized UI state management
│   └── styles.tcss            # Textual CSS styles
├── components/
│   ├── balloon_spinner.py     # Animated spinner widget
│   ├── caret.py               # Input caret indicator
│   ├── chat_history.py        # Chat message container
│   ├── flex.py                # Horizontal flex container
│   ├── header.py              # App header with MCP server status
│   ├── messages.py            # Message data models and widgets
│   ├── slash_command_menu.py  # Slash command menu with filtering
│   ├── spacer.py              # Empty spacer widget
│   ├── thinking_indicator.py  # "Agent is thinking" indicator
│   ├── tool_permission_prompt.py  # Tool permission request UI
│   └── user_input.py          # User text input widget
└── utils/
    ├── config.py              # YAML config loading
    ├── enums.py               # Shared enumerations
    ├── format_tool_input.py   # Tool input formatting
    ├── logger.py              # Logging setup
    ├── mcp_server_status.py   # MCP server connection state
    ├── system_prompt.py       # System prompt builder
    └── tool_info.py           # Tool name parsing
```

### Core Architecture

The application follows a loosely coupled architecture with four main orchestration objects:

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentChatCLIApp                         │
│  ┌───────────┐  ┌───────────┐  ┌─────────┐  ┌───────────┐  │
│  │  UIState  │  │  Renderer   │  │ Actions │  │ AgentLoop │  │
│  └─────┬─────┘  └─────┬─────┘  └────┬────┘  └─────┬─────┘  │
│        │              │             │              │        │
│        └──────────────┴─────────────┴──────────────┘        │
│                            │                                 │
│  ┌─────────────────────────┴─────────────────────────────┐  │
│  │                    Components                          │  │
│  │  Header │ ChatHistory │ ThinkingIndicator │ UserInput │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

**UIState** (`core/ui_state.py`)
Centralized management of UI state behaviors. Handles:
- Thinking indicator visibility and cursor blink state
- Tool permission prompt display/hide
- Interrupt state tracking

This class was introduced in PR #9 to consolidate scattered UI state logic from Actions and Renderer into a single cohesive module.

**Renderer** (`core/renderer.py`)
Routes messages from the AgentLoop to appropriate UI components:
- `STREAM_EVENT`: Streaming text chunks to AgentMessage widgets
- `ASSISTANT`: Complete assistant responses with tool use blocks
- `SYSTEM` / `USER`: System and user messages
- `TOOL_PERMISSION_REQUEST`: Triggers permission prompt UI
- `RESULT`: Signals completion, resets state

**Actions** (`core/actions.py`)
User-initiated action handlers:
- `post_user_message()`: Posts user message and queries agent
- `interrupt()`: Cancels current agent operation
- `new()`: Starts new conversation, clears history
- `respond_to_tool_permission()`: Handles permission prompt responses

**AgentLoop** (`core/agent_loop.py`)
Manages the Claude Agent SDK client lifecycle:
- Initializes `ClaudeSDKClient` with config and MCP servers
- Processes incoming messages via async generator
- Handles tool permission flow via `_can_use_tool()` callback
- Manages `query_queue` and `permission_response_queue` for async communication

### Message Flow

1. User types in `UserInput` and presses Enter
2. `Actions.post_user_message()` posts to UI and enqueues to `AgentLoop.query_queue`
3. `AgentLoop` sends query to Claude Agent SDK and streams responses
4. Responses flow through `Actions.render_message()` to update UI
5. Tool use triggers permission prompt via `UIState.show_permission_prompt()`
6. User response flows back through `Actions.respond_to_tool_permission()`

### Components

**UserInput** (`components/user_input.py`)
Text input with:
- Enter to submit
- Ctrl+J for newlines
- `/` opens slash command menu

**SlashCommandMenu** (`components/slash_command_menu.py`)
Command menu triggered by `/`:
- Fuzzy filtering as you type (text shows in input)
- Commands: `/new`, `/clear`, `/exit`
- Backspace removes filter chars; closes menu when empty
- Escape closes and clears

**ToolPermissionPrompt** (`components/tool_permission_prompt.py`)
Modal prompt for tool permission requests:
- Shows tool name and MCP server
- Enter to allow, ESC to deny, or type custom response
- Manages focus to prevent input elsewhere while visible

**ChatHistory** (`components/chat_history.py`)
Container for message widgets.

**ThinkingIndicator** (`components/thinking_indicator.py`)
Animated indicator shown during agent processing.

**Header** (`components/header.py`)
Displays available MCP servers with connection status via `MCPServerStatus` subscription.

### Configuration

Configuration is loaded from `agent-chat-cli.config.yaml`:

```yaml
system_prompt: "prompt.md"  # File path or literal string
model: "claude-sonnet-4-20250514"
permission_mode: "bypass_permissions"

mcp_servers:
  server_name:
    description: "Server description"
    command: "npx"
    args: ["-y", "@some/mcp-server"]
    env:
      API_KEY: "$API_KEY"
    enabled: true
    prompt: "server_prompt.md"

agents:
  agent_name:
    description: "Agent description"
    prompt: "agent_prompt.md"
    tools: ["tool1", "tool2"]
```

### Key Patterns

**Reactive Properties**: Textual's `reactive` and `var` are used for automatic UI updates when state changes (e.g., `ThinkingIndicator.is_thinking`, `ToolPermissionPrompt.is_visible`).

**Async Queues**: Communication between UI and AgentLoop uses `asyncio.Queue` for decoupled async message passing.

**Observer Pattern**: `MCPServerStatus` uses callback subscriptions to notify components of connection state changes.

**TYPE_CHECKING Guards**: Circular import prevention via `if TYPE_CHECKING:` blocks for type hints.

### Testing

Tests use pytest with pytest-asyncio for async support and Textual's pilot testing framework for UI interactions.

```bash
make test
```
