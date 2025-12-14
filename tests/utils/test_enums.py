from agent_chat_cli.utils.enums import (
    AgentMessageType,
    ContentType,
    ControlCommand,
    Key,
)


class TestAgentMessageType:
    def test_all_message_types_have_values(self):
        assert AgentMessageType.ASSISTANT.value == "assistant"
        assert AgentMessageType.INIT.value == "init"
        assert AgentMessageType.RESULT.value == "result"
        assert AgentMessageType.STREAM_EVENT.value == "stream_event"
        assert AgentMessageType.SYSTEM.value == "system"
        assert (
            AgentMessageType.TOOL_PERMISSION_REQUEST.value == "tool_permission_request"
        )
        assert AgentMessageType.USER.value == "user"


class TestContentType:
    def test_all_content_types_have_values(self):
        assert ContentType.TEXT.value == "text"
        assert ContentType.TOOL_USE.value == "tool_use"
        assert ContentType.CONTENT_BLOCK_DELTA.value == "content_block_delta"
        assert ContentType.TEXT_DELTA.value == "text_delta"


class TestControlCommand:
    def test_all_control_commands_have_values(self):
        assert ControlCommand.NEW_CONVERSATION.value == "new_conversation"
        assert ControlCommand.EXIT.value == "exit"
        assert ControlCommand.CLEAR.value == "clear"


class TestKey:
    def test_all_keys_have_values(self):
        assert Key.ENTER.value == "enter"
        assert Key.ESCAPE.value == "escape"
        assert Key.BACKSPACE.value == "backspace"
        assert Key.DELETE.value == "delete"
        assert Key.CTRL_J.value == "ctrl+j"
        assert Key.SLASH.value == "/"
