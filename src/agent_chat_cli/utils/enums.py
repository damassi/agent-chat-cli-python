from enum import Enum


class AgentMessageType(Enum):
    ASSISTANT = "assistant"
    INIT = "init"
    RESULT = "result"
    STREAM_EVENT = "stream_event"
    SYSTEM = "system"
    TOOL_PERMISSION_REQUEST = "tool_permission_request"
    USER = "user"


class ContentType(Enum):
    TEXT = "text"
    TOOL_USE = "tool_use"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    TEXT_DELTA = "text_delta"


class ControlCommand(Enum):
    NEW_CONVERSATION = "new_conversation"
    EXIT = "exit"
    CLEAR = "clear"


class Key(Enum):
    ENTER = "enter"
    ESCAPE = "escape"
    BACKSPACE = "backspace"
    DELETE = "delete"
    CTRL_J = "ctrl+j"
    SLASH = "/"
