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
- **ToolPermissionPrompt**: Interactive widget for approving/denying tool execution requests

### System Layer

#### Agent Loop (`system/agent_loop.py`)
Manages the conversation loop with Claude SDK:
- Maintains async queue for user queries
- Handles streaming responses
- Parses SDK messages into structured AgentMessage objects
- Emits AgentMessageType events (STREAM_EVENT, ASSISTANT, RESULT)
- Manages session persistence via session_id
- Implements `_can_use_tool` callback for interactive tool permission requests
- Uses `permission_lock` (asyncio.Lock) to serialize parallel permission requests
- Manages `permission_response_queue` for user responses to tool permission prompts

#### Message Bus (`system/message_bus.py`)
Routes agent messages to appropriate UI components:
- Handles streaming text updates
- Mounts tool use messages
- Controls thinking indicator state
- Manages scroll-to-bottom behavior
- Displays system messages (e.g., MCP server connection notifications)
- Detects tool permission requests and shows ToolPermissionPrompt
- Manages UI transitions between UserInput and ToolPermissionPrompt

#### Actions (`system/actions.py`)
Centralizes all user-initiated actions and controls:
- **quit()**: Exits the application
- **query(user_input)**: Sends user query to agent loop queue
- **interrupt()**: Stops streaming mid-execution by setting interrupt flag and calling SDK interrupt (ignores ESC when tool permission prompt is visible)
- **new()**: Starts new conversation by sending NEW_CONVERSATION control command
- **respond_to_tool_permission(response)**: Handles tool permission responses, manages UI state transitions between permission prompt and user input
- Manages UI state (thinking indicator, chat history clearing)
- Directly accesses agent_loop internals (query_queue, client, interrupting flag, permission_response_queue)

Actions are triggered via:
- Keybindings in app.py (ESC → action_interrupt, Ctrl+N → action_new)
- Text commands in user_input.py ("exit", "clear")
- Component events (ToolPermissionPrompt.on_input_submitted → respond_to_tool_permission)

### Utils Layer

#### Config (`utils/config.py`)
Loads and validates YAML configuration:
- Filters disabled MCP servers
- Loads prompts from files
- Expands environment variables
- Combines system prompt with MCP server prompts
- Provides `get_sdk_config()` to filter app-specific config before passing to SDK

## Data Flow

### Standard Query Flow

```
User Input
    ↓
UserInput.on_input_submitted
    ↓
MessagePosted event → ChatHistory (immediate UI update)
    ↓
Actions.query(user_input) → AgentLoop.query_queue.put()
    ↓
Claude SDK (all enabled servers pre-connected at startup)
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
- **mcp_servers**: MCP server configurations (filtered by enabled flag)
- **agents**: Named agent configurations
- **disallowed_tools**: Tool filtering
- **permission_mode**: Permission handling mode

MCP server prompts are automatically appended to the system prompt. All enabled MCP servers are loaded at startup.

## Tool Permission System

The application implements interactive tool permission requests that allow users to approve or deny tool execution in real-time.

### Components

#### ToolPermissionPrompt (`components/tool_permission_prompt.py`)
Textual widget that displays permission requests to the user:
- Shows tool name with MCP server info
- Provides input field for user response
- Supports Enter (approve), ESC (deny), or custom text responses

### Permission Flow

```
Tool Execution Request (from Claude SDK)
    ↓
AgentLoop._can_use_tool (callback with permission_lock acquired)
    ↓
Emit SYSTEM AgentMessage with tool_permission_request data
    ↓
MessageBus._handle_system detects permission request
    ↓
Show ToolPermissionPrompt, hide UserInput
    ↓
User Response:
    - Enter (or "yes") → Approve
    - ESC (or "no") → Deny
    - Custom text → Send to Claude as alternative instruction
    ↓
Actions.respond_to_tool_permission(response)
    ↓
Put response on permission_response_queue
    ↓
Hide ToolPermissionPrompt, show UserInput
    ↓
AgentLoop._can_use_tool receives response
    ↓
Return PermissionResultAllow or PermissionResultDeny
    ↓
Next tool permission request (if multiple tools called)
```

### Serialization with Permission Lock

When multiple tools request permission in parallel, a `permission_lock` (asyncio.Lock) ensures they are handled sequentially:

1. First tool acquires lock → Shows prompt → Waits for response → Releases lock
2. Second tool acquires lock → Shows prompt → Waits for response → Releases lock
3. Third tool acquires lock → Shows prompt → Waits for response → Releases lock

This prevents race conditions where multiple prompts would overwrite each other and ensures each tool gets a dedicated user response.

### Permission Responses

The `_can_use_tool` callback returns typed permission results:

**Approve (CONFIRM)**:
```python
return PermissionResultAllow(
    behavior="allow",
    updated_input=tool_input,
)
```

**Deny (DENY)**:
```python
return PermissionResultDeny(
    behavior="deny",
    message="User denied permission",
    interrupt=True,
)
```

**Custom Response**:
```python
return PermissionResultDeny(
    behavior="deny",
    message=user_response,  # Alternative instruction sent to Claude
    interrupt=True,
)
```

### ESC Key Handling

When ToolPermissionPrompt is visible, the ESC key is intercepted:
- `Actions.interrupt()` checks `permission_prompt.is_visible`
- If visible, returns early without interrupting the agent
- ToolPermissionPrompt's `on_key` handler processes ESC to deny the tool
- If not visible, ESC performs normal interrupt behavior

### System Messages

Permission denials generate system messages in the chat:
- **Denied**: `"Permission denied for {tool_name}"`
- **Custom response**: `"Custom response for {tool_name}: {user_response}"`

## User Commands

### Text Commands
- **exit**: Quits the application
- **clear**: Starts a new conversation (clears history and reconnects)

### Keybindings
- **Ctrl+C**: Quit application
- **ESC**: Interrupt streaming response (or deny tool permission if prompt visible)
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
- Tool permission requests are serialized via asyncio.Lock to handle parallel tool calls sequentially
- Permission responses use typed SDK objects (PermissionResultAllow, PermissionResultDeny) rather than plain dictionaries
