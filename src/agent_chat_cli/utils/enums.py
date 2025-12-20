from enum import Enum
from typing import NamedTuple


class AppEventType(Enum):
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
    CHANGE_MODEL = "change_model"
    EXIT = "exit"
    CLEAR = "clear"


class ModelChangeCommand(NamedTuple):
    command: ControlCommand
    model: str


class Key(Enum):
    ENTER = "enter"
    ESCAPE = "escape"
    BACKSPACE = "backspace"
    DELETE = "delete"
    CTRL_J = "ctrl+j"
    SLASH = "/"
