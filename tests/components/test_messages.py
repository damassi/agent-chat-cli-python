from agent_chat_cli.components.messages import Message, MessageType


class TestMessage:
    def test_system_creates_system_message(self):
        msg = Message.system("System alert")

        assert msg.type == MessageType.SYSTEM
        assert msg.content == "System alert"
        assert msg.metadata is None

    def test_user_creates_user_message(self):
        msg = Message.user("Hello there")

        assert msg.type == MessageType.USER
        assert msg.content == "Hello there"
        assert msg.metadata is None

    def test_agent_creates_agent_message(self):
        msg = Message.agent("I can help with that.")

        assert msg.type == MessageType.AGENT
        assert msg.content == "I can help with that."
        assert msg.metadata is None

    def test_tool_creates_tool_message_with_metadata(self):
        msg = Message.tool("read_file", '{"path": "/tmp/test.txt"}')

        assert msg.type == MessageType.TOOL
        assert msg.content == '{"path": "/tmp/test.txt"}'
        assert msg.metadata == {"tool_name": "read_file"}


class TestMessageType:
    def test_all_types_have_values(self):
        assert MessageType.SYSTEM.value == "system"
        assert MessageType.USER.value == "user"
        assert MessageType.AGENT.value == "agent"
        assert MessageType.TOOL.value == "tool"
