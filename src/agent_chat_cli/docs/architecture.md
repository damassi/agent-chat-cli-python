# Architecture

## Overview

Agent Chat CLI is a Python TUI application built with Textual that provides an interactive chat interface for Claude AI with MCP (Model Context Protocol) server support.

## Directory Structure

```
src/agent_chat_cli/
├── app.py                      # Main application entry point
├── components/                 # UI components (Textual widgets)
│   ├── chat_history.py        # Container for chat messages
│   ├── messages.py            # Message widgets and UI Message type
│   ├── user_input.py          # User input component
│   ├── thinking_indicator.py # Loading indicator
│   └── header.py              # App header with config info
├── utils/                     # Business logic and utilities
│   ├── agent_loop.py          # Claude SDK conversation loop
│   ├── message_bus.py         # Routes messages between agent and UI
│   ├── config.py              # Configuration loading and validation
│   ├── enums.py               # All enum types
│   ├── system_prompt.py       # System prompt assembly
│   ├── format_tool_input.py   # Tool input formatting
│   └── tool_info.py           # MCP tool name parsing
└── utils/styles.tcss          # Textual CSS styles
```

## Core Components

### App Layer (`app.py`)
Main Textual application that initializes and coordinates all components.

### Components Layer
Textual widgets responsible for UI rendering:
- **ChatHistory**: Container that displays message widgets
- **Message widgets**: SystemMessage, UserMessage, AgentMessage, ToolMessage
- **UserInput**: Handles user text input and submission
- **ThinkingIndicator**: Shows when agent is processing

### Utils Layer

#### Agent Loop (`agent_loop.py`)
Manages the conversation loop with Claude SDK:
- Maintains async queue for user queries
- Handles streaming responses
- Parses SDK messages into structured AgentMessage objects
- Emits AgentMessageType events (STREAM_EVENT, ASSISTANT, RESULT)

#### Message Bus (`message_bus.py`)
Routes agent messages to appropriate UI components:
- Handles streaming text updates
- Mounts tool use messages
- Controls thinking indicator state
- Manages scroll-to-bottom behavior

#### Config (`config.py`)
Loads and validates YAML configuration:
- Filters disabled MCP servers
- Loads prompts from files
- Expands environment variables
- Combines system prompt with MCP server prompts

## Data Flow

```
User Input
    ↓
UserInput.on_input_submitted
    ↓
MessagePosted event → ChatHistory (immediate UI update)
    ↓
AgentLoop.query (added to queue)
    ↓
Claude SDK (streaming response)
    ↓
AgentLoop._handle_message
    ↓
AgentMessage (typed message) → MessageBus.handle_agent_message
    ↓
Match on AgentMessageType:
    - STREAM_EVENT → Update streaming message widget
    - ASSISTANT → Mount tool use widgets
    - RESULT → Reset thinking indicator
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
- **include_partial_messages**: Enable streaming
- **mcp_servers**: MCP server configurations (filtered by enabled flag)
- **agents**: Named agent configurations
- **disallowed_tools**: Tool filtering
- **permission_mode**: Permission handling mode

MCP server prompts are automatically appended to the system prompt.

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
