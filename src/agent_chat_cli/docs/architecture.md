# Architecture

## Overview

Agent Chat CLI is a Python TUI application built with Textual that provides an interactive chat interface for Claude AI with MCP (Model Context Protocol) server support.

## Core Components

### App Layer (`app.py`)
Main Textual application that initializes and coordinates all components.

### Components Layer
Textual widgets responsible for UI rendering:
- **ChatHistory**: Container that displays message widgets
- **Message widgets**: SystemMessage, UserMessage, AgentMessage, ToolMessage
- **UserInput**: Handles user text input and submission
- **ThinkingIndicator**: Shows when agent is processing

### System Layer

#### Agent Loop (`system/agent_loop.py`)
Manages the conversation loop with Claude SDK:
- Maintains async queue for user queries
- Handles streaming responses
- Parses SDK messages into structured AgentMessage objects
- Emits AgentMessageType events (STREAM_EVENT, ASSISTANT, RESULT)
- Manages session persistence via session_id
- Supports dynamic MCP server inference and loading

#### MCP Server Inference (`system/mcp_inference.py`)
Intelligently determines which MCP servers are needed for each query:
- Uses a persistent Haiku client for fast inference (~1-3s after initial boot)
- Analyzes user queries to infer required servers
- Maintains a cached set of inferred servers across conversation
- Returns only newly needed servers to minimize reconnections
- Can be disabled via `mcp_server_inference: false` config option

#### Message Bus (`system/message_bus.py`)
Routes agent messages to appropriate UI components:
- Handles streaming text updates
- Mounts tool use messages
- Controls thinking indicator state
- Manages scroll-to-bottom behavior
- Displays system messages (e.g., MCP server connection notifications)

#### Actions (`system/actions.py`)
Centralizes all user-initiated actions and controls:
- **quit()**: Exits the application
- **query(user_input)**: Sends user query to agent loop queue
- **interrupt()**: Stops streaming mid-execution by setting interrupt flag and calling SDK interrupt
- **new()**: Starts new conversation by sending NEW_CONVERSATION control command
- Manages UI state (thinking indicator, chat history clearing)
- Directly accesses agent_loop internals (query_queue, client, interrupting flag)

Actions are triggered via:
- Keybindings in app.py (ESC → action_interrupt, Ctrl+N → action_new)
- Text commands in user_input.py ("exit", "clear")

### Utils Layer

#### Config (`utils/config.py`)
Loads and validates YAML configuration:
- Filters disabled MCP servers
- Loads prompts from files
- Expands environment variables
- Combines system prompt with MCP server prompts
- Provides `get_sdk_config()` to filter app-specific config before passing to SDK

## Data Flow

### Standard Query Flow (with MCP Inference enabled)

```
User Input
    ↓
UserInput.on_input_submitted
    ↓
MessagePosted event → ChatHistory (immediate UI update)
    ↓
Actions.query(user_input) → AgentLoop.query_queue.put()
    ↓
AgentLoop: MCP Server Inference (if enabled)
    ↓
infer_mcp_servers(user_message) → Haiku query
    ↓
If new servers needed:
    - Post SYSTEM message ("Connecting to [servers]...")
    - Disconnect client
    - Reconnect with new servers (preserving session_id)
    ↓
Claude SDK (streaming response with connected MCP tools)
    ↓
AgentLoop._handle_message
    ↓
AgentMessage (typed message) → MessageBus.handle_agent_message
    ↓
Match on AgentMessageType:
    - STREAM_EVENT → Update streaming message widget
    - ASSISTANT → Mount tool use widgets
    - SYSTEM → Display system notification
    - RESULT → Reset thinking indicator
```

### Query Flow (with MCP Inference disabled)

```
User Input
    ↓
UserInput.on_input_submitted
    ↓
MessagePosted event → ChatHistory (immediate UI update)
    ↓
Actions.query(user_input) → AgentLoop.query_queue.put()
    ↓
Claude SDK (all servers pre-connected at startup)
    ↓
[Same as above from _handle_message onwards]
```

### Control Commands Flow
```
User Action (ESC, Ctrl+N, "clear", "exit")
    ↓
App.action_* (keybinding) OR UserInput (text command)
    ↓
Actions.interrupt() OR Actions.new() OR Actions.quit()
    ↓
AgentLoop internals:
    - interrupt: Set interrupting flag + SDK interrupt
    - new: Put ControlCommand.NEW_CONVERSATION on queue
    - quit: App.exit()
```

## Key Types

### Enums (`utils/enums.py`)

**AgentMessageType**: Agent communication events
- ASSISTANT: Assistant message with content blocks
- STREAM_EVENT: Streaming text chunk
- RESULT: Response complete
- INIT, SYSTEM: Initialization and system events

**ContentType**: Content block types
- TEXT: Text content
- TOOL_USE: Tool call
- CONTENT_BLOCK_DELTA: SDK streaming event type
- TEXT_DELTA: SDK text delta type

**ControlCommand**: Control commands for agent loop
- NEW_CONVERSATION: Disconnect and reconnect SDK to start fresh session
- EXIT: User command to quit application
- CLEAR: User command to start new conversation

**MessageType** (`components/messages.py`): UI message types
- SYSTEM, USER, AGENT, TOOL

### Data Classes

**AgentMessage** (`utils/agent_loop.py`): Structured message from agent loop
```python
@dataclass
class AgentMessage:
    type: AgentMessageType
    data: Any
```

**Message** (`components/messages.py`): UI message data
```python
@dataclass
class Message:
    type: MessageType
    content: str
    metadata: dict[str, Any] | None = None
```

## Configuration System

Configuration is loaded from `agent-chat-cli.config.yaml`:
- **system_prompt**: Base system prompt (supports file paths)
- **model**: Claude model to use
- **include_partial_messages**: Enable streaming responses (default: true)
- **mcp_server_inference**: Enable dynamic MCP server inference (default: true)
  - When `true`: App boots instantly without MCP servers, connects only when needed
  - When `false`: All enabled MCP servers load at startup (traditional behavior)
- **mcp_servers**: MCP server configurations (filtered by enabled flag)
- **agents**: Named agent configurations
- **disallowed_tools**: Tool filtering
- **permission_mode**: Permission handling mode

MCP server prompts are automatically appended to the system prompt.

### MCP Server Inference

When `mcp_server_inference: true` (default):

1. **Fast Boot**: App starts without connecting to any MCP servers
2. **Smart Detection**: Before each query, Haiku analyzes which servers are needed
3. **Dynamic Loading**: Only connects to newly required servers
4. **Session Preservation**: Maintains conversation history when reconnecting with new servers
5. **Performance**: ~1-3s inference latency after initial boot (first query ~8-12s)

Example config:
```yaml
mcp_server_inference: true  # or false to disable

mcp_servers:
  github:
    description: "Search code, PRs, issues"
    enabled: true
    # ... rest of config
```

## User Commands

### Text Commands
- **exit**: Quits the application
- **clear**: Starts a new conversation (clears history and reconnects)

### Keybindings
- **Ctrl+C**: Quit application
- **ESC**: Interrupt streaming response
- **Ctrl+N**: Start new conversation

## Session Management

The agent loop supports session persistence and resumption via `session_id`:

### Initialization
- `AgentLoop.__init__` accepts an optional `session_id` parameter
- If provided, the session_id is passed to Claude SDK via the `resume` config option
- This allows resuming a previous conversation with full context

### Session Capture
- During SDK initialization, a SystemMessage with subtype "init" is received
- The message contains a `session_id` in its data payload
- AgentLoop extracts and stores this session_id: `agent_loop.py:65`
- The session_id can be persisted and used to resume the session later

### Resume Flow
```
AgentLoop(session_id="abc123")
    ↓
config_dict["resume"] = session_id
    ↓
ClaudeSDKClient initialized with resume option
    ↓
SDK reconnects to previous session with full history
```

## Event Flow

### User Message Flow
1. User submits text → UserInput
2. MessagePosted event → App
3. App → MessageBus.on_message_posted
4. MessageBus → ChatHistory.add_message
5. MessageBus → Scroll to bottom

### Agent Response Flow
1. AgentLoop receives SDK message
2. Parse into AgentMessage with AgentMessageType
3. MessageBus.handle_agent_message (match/case on type)
4. Update UI components based on type
5. Scroll to bottom

## Notes

- Two distinct MessageType enums exist for different purposes (UI vs Agent events)
- Message bus manages stateful streaming (tracks current_agent_message)
- Config loading combines multiple prompts into final system_prompt
- Tool names follow format: `mcp__servername__toolname`
- Actions class provides single interface for all user-initiated operations
- Control commands are queued alongside user queries to ensure proper task ordering
- Agent loop processes both strings (user queries) and ControlCommands from the same queue
- Interrupt flag is checked on each streaming message to enable immediate stop
